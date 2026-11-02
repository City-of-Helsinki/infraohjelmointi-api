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
   events still arrive. ``ResyncingListenerManager`` keeps live events away
   from a stream that is about to re-read, so it can't jump past the gap.

3. Publishing. With Redis configured, ``send_event`` only publishes; a failed
   publish meant even the sending process's own tabs got nothing. Now the
   event is then delivered to this process's streams directly, and publishing
   is skipped for a while so a dead Redis costs one timeout per process per
   backoff period, not one per event. Other processes get the events from the
   table when their subscribers reconnect.
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
    """ListenerManager that doesn't queue live events for a re-reading stream.

    Same as the library's ``add_to_queues`` (5.3.4) except that listeners with
    ``overflow`` set are skipped: they are about to re-read the event table,
    which has the event, and a queued newer event would move their position
    past events they haven't read yet.
    """

    def add_to_queues(self, channel, event):
        with self.lock:
            wake = []
            for listener in self.listeners_by_channel.get(channel, set()):
                if listener.overflow:
                    continue
                items = listener.channel_items.setdefault(channel, [])
                if len(items) < MAX_PENDING:
                    items.append(event)
                    wake.append(listener)
                else:
                    listener.overflow = True
            for listener in wake:
                listener.wake_threadsafe()


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
        # The event is already stored; other processes re-read it on reconnect.
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


def install():
    """Called from AppConfig.ready, before any stream starts."""
    # The stream loop imports get_events from this module on every call.
    eventstream.get_events = releasing_connections(eventstream.get_events)

    if not isinstance(views.listener_manager, ResyncingListenerManager):
        manager = ResyncingListenerManager()
        if getattr(settings, "EVENTSTREAM_REDIS", None):
            manager.redis_listener = ReconnectingRedisListener()
        # get_listener_manager() returns this module global on every call.
        views.listener_manager = manager

    if eventstream.redis_client is not None and not isinstance(eventstream.redis_client, FallbackPublisher):
        eventstream.redis_client = FallbackPublisher(eventstream.redis_client)
