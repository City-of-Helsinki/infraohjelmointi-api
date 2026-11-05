"""
Runtime fixes for django-eventstream 5.3 (installed from AppConfig.ready).

1. DB connections. An SSE stream reads the event table via ``get_events`` on
   its request's thread, and Django only closes that connection when the
   response finishes, i.e. when the browser leaves. Every open tab would hold
   a Postgres connection for hours, so ``get_events`` is wrapped to close it
   after each read, as the old Channels consumer did.

2. Redis subscription. The library's per-process subscriber relies on
   redis-py's own reconnect: events published while the connection was down
   are silently lost, and if Redis stays down the subscriber stops for good
   until the pod restarts. ``ReconnectingRedisListener`` disables redis-py's
   retries so every drop reaches its own loop, resubscribes after a pause, and
   then makes the open streams re-read the event table (the library's
   overflow path: the stream loop re-reads from its last id), so the missed
   events still arrive.

3. Order and gaps. Event ids are consecutive per channel, so
   ``ResyncingListenerManager`` knows each stream's position: an event that
   skips ids sends the stream back to the table for the missing ones, and one
   it already has is dropped. Nothing is lost when a single publish fails while
   Redis stays up for the other processes (their next event shows the gap),
   and live events can't jump a stream past events it is about to re-read.

4. Publishing. With Redis configured, ``send_event`` only publishes; a failed
   publish meant even the sending process's own tabs got nothing. Now the
   event is then delivered to this process's streams directly, and publishing
   is skipped for a while so a dead Redis costs one timeout per process per
   backoff period, not one per event. Other processes read the skipped events
   from the table once a later event or their resubscribe reaches them.
"""

import asyncio
import functools
import json
import logging
import random
import socket
import time

from django.conf import settings
from django.db import connections
from django_eventstream import eventstream, views
from django_eventstream.event import Event
from django_eventstream.views import MAX_PENDING, ListenerManager, RedisListener

logger = logging.getLogger(__name__)

RETRY_SECONDS = 5
PUBLISH_BACKOFF_SECONDS = 30
# Re-reads after a reconnect are spread out so every open tab doesn't open a
# DB connection at the same moment.
RESYNC_SPREAD_SECONDS = 2.0

# Notice a connection that died without a FIN (NAT, failover) within about a
# minute instead of the OS default of two hours; the subscriber has no read
# timeout, so this is what detects it.
KEEPALIVE_OPTIONS = {
    option: value
    for name, value in (("TCP_KEEPIDLE", 30), ("TCP_KEEPINTVL", 10), ("TCP_KEEPCNT", 3))
    if (option := getattr(socket, name, None)) is not None
}


class ReconnectingRedisListener(RedisListener):
    def __init__(self):
        from redis.asyncio import Redis
        from redis.asyncio.retry import Retry
        from redis.backoff import NoBackoff

        # The settings are tuned for the publishing side (send_event in request
        # threads). The subscription is idle between events, so it gets no read
        # timeout but TCP keepalive probes, and no redis-py retries: a silent
        # reconnect would skip the resync below and lose what was published
        # meanwhile.
        kwargs = {
            **settings.EVENTSTREAM_REDIS,
            "socket_timeout": None,
            "socket_keepalive": True,
            "socket_keepalive_options": KEEPALIVE_OPTIONS,
            "retry": Retry(NoBackoff(), 0),
        }
        self.redis_client = Redis(**kwargs)
        self.pubsub = None

    async def start(self):
        while True:
            self.pubsub = self.redis_client.pubsub()
            try:
                await self.listen()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.warning(
                    "SSE Redis subscription lost; resubscribing in %ss", RETRY_SECONDS,
                    exc_info=True,
                )
            finally:
                try:
                    await self.pubsub.aclose()
                except Exception:
                    pass
            await asyncio.sleep(RETRY_SECONDS)

    async def listen(self):
        # Subscribe before resyncing, so nothing published from here on is missed.
        # The base class subscribes again, which costs one harmless round trip.
        await self.pubsub.subscribe("events_channel")
        resync_open_streams()
        await super().listen()


class ResyncingListenerManager(ListenerManager):
    """ListenerManager that delivers every stored event once and in order.

    Same as the library's ``add_to_queues`` (5.3.4), plus:

    - Listeners with ``overflow`` set are skipped: they are about to re-read
      the event table, which has the event, and a queued newer event would
      move their position past events they haven't read yet.
    - A stream's position (``listener.positions``, recorded by
      ``recording_positions``) is compared with the event id. Ids are
      consecutive per channel, so a jump means an event never arrived here,
      e.g. its publish failed in another process while Redis stayed up for
      this one; the stream then re-reads the table from its position instead
      of skipping it. An id at or below the position was delivered already
      (by a re-read, or both locally and through Redis) and is dropped.
    """

    def add_to_queues(self, channel, event):
        with self.lock:
            wake = []
            for listener in self.listeners_by_channel.get(channel, set()):
                if listener.overflow:
                    continue
                verdict = _check_position(listener, channel, event)
                if verdict == "delivered":
                    continue
                if verdict == "gap":
                    listener.overflow = True
                    wake.append(listener)
                    continue
                items = listener.channel_items.setdefault(channel, [])
                if len(items) < MAX_PENDING:
                    items.append(event)
                    wake.append(listener)
                else:
                    listener.overflow = True
            for listener in wake:
                listener.wake_threadsafe()


def _check_position(listener, channel, event):
    """'next', 'gap' or 'delivered' for ``event`` on this stream; 'next' also
    advances the position. Unknown positions or ids always count as 'next'."""
    positions = getattr(listener, "positions", None)
    if not positions or positions.get(channel) is None or event.id is None:
        return "next"
    event_id = int(event.id)
    position = positions[channel]
    if event_id <= position:
        return "delivered"
    if event_id > position + 1:
        return "gap"
    positions[channel] = event_id
    return "next"


def resync_open_streams():
    """Make every open stream in this process re-read the event table."""
    listener_manager = views.get_listener_manager()
    with listener_manager.lock:
        listeners = {
            listener
            for channel_listeners in listener_manager.listeners_by_channel.values()
            for listener in channel_listeners
        }
        for listener in listeners:
            # Queued events are in the table too; the re-read delivers them in order.
            listener.channel_items = {}
            listener.overflow = True
    for listener in listeners:
        delay = random.uniform(0, RESYNC_SPREAD_SECONDS)
        listener.loop.call_soon_threadsafe(listener.loop.call_later, delay, listener.aevent.set)


class FallbackPublisher:
    """Stands in for eventstream's module-level Redis client (send_event)."""

    def __init__(self, client):
        self.client = client
        self.skip_until = 0.0

    def publish(self, channel_name, message):
        if time.monotonic() >= self.skip_until:
            try:
                return self.client.publish(channel_name, message)
            except Exception:
                self.skip_until = time.monotonic() + PUBLISH_BACKOFF_SECONDS
                logger.warning(
                    "SSE publish to Redis failed; delivering to this process only for %ss",
                    PUBLISH_BACKOFF_SECONDS, exc_info=True,
                )
        # The event is already stored; other processes read it from the table
        # when their next event shows the gap (ResyncingListenerManager).
        payload = json.loads(message)
        views.get_listener_manager().add_to_queues(
            payload["channel"],
            Event(payload["channel"], payload["event_type"], payload["data"], id=payload["pub_id"]),
        )
        return 0


def releasing_connections(get_events):
    """Wrap get_events so the DB connections it opens are closed afterwards."""
    if getattr(get_events, "releases_connections", False):
        return get_events

    @functools.wraps(get_events)
    def wrapper(*args, **kwargs):
        try:
            return get_events(*args, **kwargs)
        finally:
            # Unconditional: close_old_connections would keep them under CONN_MAX_AGE.
            connections.close_all()

    wrapper.releases_connections = True
    return wrapper


def recording_positions(get_events):
    """Wrap get_events so a stream's listener knows how far each read got.

    ``linking_listener`` puts the listener on the request. The position is the
    last event id the read returned, or the channel's current id when it
    returned none: where the stream loop continues from.

    The position also goes on the request right away. The library only stores
    it there when the stream starts waiting, so the re-read it does when events
    were queued during a read started from the request's original ids; for a
    browser that connected without Last-Event-ID that meant "from now", and
    those queued events were lost.
    """
    if getattr(get_events, "records_positions", False):
        return get_events

    @functools.wraps(get_events)
    def wrapper(request, *args, **kwargs):
        response = get_events(request, *args, **kwargs)
        listener = getattr(request, "listener", None)
        if listener is not None:
            positions = {}
            for channel in request.channels:
                items = response.channel_items.get(channel) or []
                last_id = items[-1].id if items else response.channel_last_ids.get(channel)
                positions[channel] = int(last_id) if last_id is not None else None
            with views.get_listener_manager().lock:
                listener.positions = positions
            request.channel_last_ids = {
                channel: str(position) for channel, position in positions.items()
                if position is not None
            }
        return response

    wrapper.records_positions = True
    return wrapper


def linking_listener(stream):
    """Wrap the view's stream() so get_events can find the request's listener."""
    if getattr(stream, "links_listener", False):
        return stream

    @functools.wraps(stream)
    def wrapper(event_request, listener):
        event_request.listener = listener
        return stream(event_request, listener)

    wrapper.links_listener = True
    return wrapper


def install():
    """Called from AppConfig.ready, before any stream starts."""
    # The stream loop imports get_events from this module on every call, and
    # the events view looks stream up in its module on every request.
    eventstream.get_events = releasing_connections(recording_positions(eventstream.get_events))
    views.stream = linking_listener(views.stream)

    if not isinstance(views.listener_manager, ResyncingListenerManager):
        manager = ResyncingListenerManager()
        if getattr(settings, "EVENTSTREAM_REDIS", None):
            manager.redis_listener = ReconnectingRedisListener()
        # get_listener_manager() returns this module global on every call.
        views.listener_manager = manager

    if eventstream.redis_client is not None and not isinstance(eventstream.redis_client, FallbackPublisher):
        eventstream.redis_client = FallbackPublisher(eventstream.redis_client)
