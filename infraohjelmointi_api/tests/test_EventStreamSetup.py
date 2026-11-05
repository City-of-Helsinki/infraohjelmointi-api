"""django-eventstream 5 wiring: the /events/ route, the Redis settings and
the reconnecting pub/sub listener and connection handling
(utils/eventstream_setup.py)."""

import asyncio
import json
from unittest.mock import Mock, patch

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import connections
from django.test import RequestFactory, SimpleTestCase, TransactionTestCase, override_settings
from django.urls import resolve
from django_eventstream.event import Event
from django_eventstream.utils import get_storage
from django_eventstream import views
from django_eventstream.views import Listener, events, get_listener_manager

from infraohjelmointi_api.utils import eventstream_setup
from infraohjelmointi_api.utils.eventstream_setup import (
    FallbackPublisher,
    ReconnectingRedisListener,
    ResyncingListenerManager,
)
from project.settings import _eventstream_redis_kwargs


class EventsRouteTests(SimpleTestCase):
    def test_events_url_serves_both_channels(self):
        match = resolve("/events/")

        self.assertIs(match.func, events)
        self.assertEqual(match.kwargs, {"channels": ["finance", "project"]})


class RedisSettingsTests(SimpleTestCase):
    def test_parses_the_platta_url_with_timeouts_and_no_retries(self):
        kwargs = _eventstream_redis_kwargs("redis://redis:6379/1")
        retry = kwargs.pop("retry")

        self.assertEqual(
            kwargs,
            {
                "host": "redis", "port": 6379, "db": 1,
                "socket_connect_timeout": 1, "socket_timeout": 2, "socket_keepalive": True,
            },
        )
        # redis-py's default retries held a request for 15 s with Redis down.
        self.assertEqual(retry.get_retries(), 0)

    def test_passes_credentials_and_tls(self):
        kwargs = _eventstream_redis_kwargs("rediss://user:secret@cache.example:6380")

        self.assertEqual(
            (kwargs["host"], kwargs["port"], kwargs["db"], kwargs["username"], kwargs["password"], kwargs["ssl"]),
            ("cache.example", 6380, 0, "user", "secret", True),
        )

    def test_decodes_escaped_credentials(self):
        kwargs = _eventstream_redis_kwargs("redis://user:p%40ss%2Fword@redis:6379/0")

        self.assertEqual(kwargs["password"], "p@ss/word")


class FakePubSub:
    """Stands in for redis.asyncio PubSub; ``messages`` drives listen().

    An exception is raised, an asyncio.Event is waited for, anything else is
    yielded as a message.
    """

    def __init__(self, messages):
        self.messages = messages
        self.subscribed = []

    async def subscribe(self, channel):
        self.subscribed.append(channel)

    async def listen(self):
        for message in self.messages:
            if isinstance(message, Exception):
                raise message
            if isinstance(message, asyncio.Event):
                await message.wait()
                continue
            yield message
        await asyncio.Event().wait()  # an idle, healthy subscription

    async def aclose(self):
        pass


class FakeRedis:
    def __init__(self, pubsubs):
        self._pubsubs = iter(pubsubs)

    def pubsub(self):
        return next(self._pubsubs)


@override_settings(EVENTSTREAM_REDIS=_eventstream_redis_kwargs("redis://localhost:6379/0"))
class ReconnectingRedisListenerTests(SimpleTestCase):
    def test_subscriber_has_no_read_timeout_but_keepalive_probes(self):
        kwargs = ReconnectingRedisListener().redis_client.connection_pool.connection_kwargs

        self.assertIsNone(kwargs["socket_timeout"])
        self.assertTrue(kwargs["socket_keepalive"])
        self.assertEqual(kwargs["socket_keepalive_options"], eventstream_setup.KEEPALIVE_OPTIONS)
        # A silent redis-py reconnect would skip the resync and lose events.
        self.assertEqual(kwargs["retry"].get_retries(), 0)

    def test_resubscribes_after_a_lost_connection_and_resyncs_open_streams(self):
        message = {
            "type": "message",
            "data": '{"channel": "finance", "event_type": "finance-update", "data": "{}", "pub_id": "7"}',
        }
        reread_done = asyncio.Event()
        first = FakePubSub([ConnectionError("Redis restarted")])
        second = FakePubSub([reread_done, message])

        async def scenario():
            stream = Listener()
            stream.channels = {"finance"}
            stream.assign_loop()
            # redis_listener is patched out below, so add_listener starts no
            # subscriber of its own; this test drives one directly.
            get_listener_manager().add_listener(stream)
            stream.channel_items = {"finance": [Event("finance", "stale", "{}", id="1")]}
            subscriber = ReconnectingRedisListener()
            subscriber.redis_client = FakeRedis([first, second])
            try:
                with patch.object(eventstream_setup, "RETRY_SECONDS", 0), \
                        patch.object(eventstream_setup, "RESYNC_SPREAD_SECONDS", 0):
                    task = asyncio.ensure_future(subscriber.start())
                    await asyncio.wait_for(stream.aevent.wait(), 1)
                    told_to_reread = stream.overflow
                    queued_meanwhile = dict(stream.channel_items)
                    # The stream loop re-reads the table and clears the flag.
                    stream.overflow = False
                    reread_done.set()
                    for _ in range(50):
                        await asyncio.sleep(0.01)
                        if stream.channel_items.get("finance"):
                            break
                    task.cancel()
                return stream, told_to_reread, queued_meanwhile
            finally:
                get_listener_manager().remove_listener(stream)

        with patch.object(get_listener_manager(), "redis_listener", None), \
                self.assertLogs(eventstream_setup.logger, "WARNING"):
            stream, told_to_reread, queued_meanwhile = asyncio.run(scenario())

        self.assertEqual(first.subscribed[:1], ["events_channel"])
        self.assertEqual(second.subscribed[:1], ["events_channel"])
        # After subscribing the stream is woken to re-read the event table, and
        # its queue is dropped since the table has those events too...
        self.assertTrue(told_to_reread)
        self.assertEqual(queued_meanwhile, {})
        # ...and the reconnected subscription delivers live events again.
        self.assertEqual([e.type for e in stream.channel_items["finance"]], ["finance-update"])


class ResyncingListenerManagerTests(SimpleTestCase):
    def test_is_installed(self):
        self.assertIsInstance(get_listener_manager(), ResyncingListenerManager)

    def test_skips_streams_that_are_about_to_reread(self):
        manager = ResyncingListenerManager()
        live, rereading = Listener(), Listener()
        for listener in (live, rereading):
            listener.channels = {"finance"}
            listener.wake_threadsafe = Mock()
            manager.listeners_by_channel.setdefault("finance", set()).add(listener)
        rereading.overflow = True

        manager.add_to_queues("finance", Event("finance", "finance-update", "{}", id="8"))

        self.assertEqual([e.id for e in live.channel_items["finance"]], ["8"])
        live.wake_threadsafe.assert_called_once()
        self.assertEqual(rereading.channel_items, {})
        rereading.wake_threadsafe.assert_not_called()

    def stream_at(self, manager, position):
        listener = Listener()
        listener.channels = {"finance"}
        listener.wake_threadsafe = Mock()
        listener.positions = {"finance": position}
        manager.listeners_by_channel.setdefault("finance", set()).add(listener)
        return listener

    def test_queues_the_next_event_and_advances_the_position(self):
        manager = ResyncingListenerManager()
        stream = self.stream_at(manager, 4)

        manager.add_to_queues("finance", Event("finance", "finance-update", "{}", id="5"))

        self.assertEqual([e.id for e in stream.channel_items["finance"]], ["5"])
        self.assertEqual(stream.positions["finance"], 5)

    def test_drops_an_event_the_stream_already_has(self):
        # e.g. a publish that timed out after reaching Redis: the sending
        # process delivered it locally and then got it from Redis too.
        manager = ResyncingListenerManager()
        stream = self.stream_at(manager, 5)

        manager.add_to_queues("finance", Event("finance", "finance-update", "{}", id="5"))

        self.assertEqual(stream.channel_items, {})
        stream.wake_threadsafe.assert_not_called()

    def test_sends_the_stream_back_to_the_table_on_a_gap(self):
        manager = ResyncingListenerManager()
        stream = self.stream_at(manager, 4)

        manager.add_to_queues("finance", Event("finance", "finance-update", "{}", id="6"))

        self.assertTrue(stream.overflow)
        self.assertEqual(stream.channel_items, {})
        stream.wake_threadsafe.assert_called_once()
        self.assertEqual(stream.positions["finance"], 4)


class StreamGapTests(TransactionTestCase):
    """The real stream loop and event table (TransactionTestCase: the loop
    reads the table on another thread)."""

    def deliveries(self, publish_events, wait_first):
        """Open a stream, run ``publish_events`` (returns the event to hand to
        this process's subscriber) and return the event types the stream sent.

        With ``wait_first`` the stream is idle in its wait loop first;
        otherwise it is still right after its first read.
        """
        request = RequestFactory().get("/events/")
        request.user = AnonymousUser()

        async def scenario():
            content = events(request, channels=["finance"]).streaming_content
            try:
                body = (await anext(content)).decode()  # stream-open
                if wait_first:
                    pending = asyncio.ensure_future(anext(content))
                    await asyncio.sleep(0.3)
                event = await sync_to_async(publish_events)()
                # What this process's subscriber does with a published event.
                get_listener_manager().add_to_queues(
                    "finance", Event("finance", event.type, event.data, id=str(event.id))
                )
                if not wait_first:
                    # The stream resumes only now and finds the event queued.
                    pending = asyncio.ensure_future(anext(content))
                while event.type not in body:
                    body += (await asyncio.wait_for(pending, 5)).decode()
                    pending = asyncio.ensure_future(anext(content))
                pending.cancel()
            finally:
                await content.aclose()
                await sync_to_async(connections.close_all)()
            return body

        with patch.object(get_listener_manager(), "redis_listener", None):
            body = asyncio.run(scenario())
        return [
            line.removeprefix("event: ") for line in body.splitlines()
            if line.startswith("event: ") and line not in ("event: stream-open", "event: keep-alive")
        ]

    @staticmethod
    def store(event_type):
        return get_storage().append_event("finance", event_type, json.dumps({}))

    def test_an_event_whose_publish_was_lost_still_reaches_the_stream(self):
        """One worker's publish fails while Redis stays up for the others: the
        open stream gets the lost event from the table, before the next one."""
        def lost_then_healthy():
            self.store("lost-publish")
            return self.store("healthy-publish")

        self.assertEqual(
            self.deliveries(lost_then_healthy, wait_first=True),
            ["lost-publish", "healthy-publish"],
        )

    def test_an_event_right_after_the_stream_opens_is_not_lost(self):
        """The library re-reads when events were queued during a read; without
        a Last-Event-ID that re-read used to start from "now"."""
        self.assertEqual(
            self.deliveries(lambda: self.store("first-event"), wait_first=False),
            ["first-event"],
        )


class FallbackPublisherTests(SimpleTestCase):
    message = json.dumps({"channel": "finance", "event_type": "finance-update", "data": "{}", "pub_id": "9"})

    def test_publishes_to_redis_when_it_works(self):
        client = Mock()
        client.publish.return_value = 2

        with patch.object(get_listener_manager(), "add_to_queues") as local:
            self.assertEqual(FallbackPublisher(client).publish("events_channel", self.message), 2)

        client.publish.assert_called_once_with("events_channel", self.message)
        local.assert_not_called()

    def test_delivers_locally_and_backs_off_when_redis_fails(self):
        client = Mock()
        client.publish.side_effect = ConnectionError("Redis down")
        publisher = FallbackPublisher(client)

        with patch.object(get_listener_manager(), "add_to_queues") as local, \
                self.assertLogs(eventstream_setup.logger, "WARNING"):
            publisher.publish("events_channel", self.message)
            publisher.publish("events_channel", self.message)

        # One timeout per backoff period, not one per event.
        client.publish.assert_called_once()
        self.assertEqual(local.call_count, 2)
        channel, event = local.call_args.args
        self.assertEqual((channel, event.type, event.id), ("finance", "finance-update", "9"))


class ConnectionReleaseTests(SimpleTestCase):
    """An open stream must not hold a DB connection between its reads."""

    def test_installed_at_startup_on_the_function_the_stream_loop_calls(self):
        from django_eventstream import eventstream

        self.assertTrue(getattr(eventstream.get_events, "releases_connections", False))
        self.assertTrue(getattr(eventstream.get_events, "records_positions", False))
        self.assertTrue(getattr(views.stream, "links_listener", False))

    def test_releases_the_connection_even_when_the_read_fails(self):
        def failing_read(*args, **kwargs):
            raise RuntimeError("database went away")

        with patch.object(eventstream_setup.connections, "close_all") as close:
            with self.assertRaises(RuntimeError):
                eventstream_setup.releasing_connections(failing_read)()

        close.assert_called_once()

    def test_wraps_only_once(self):
        wrapped = eventstream_setup.releasing_connections(lambda: "events")

        self.assertIs(eventstream_setup.releasing_connections(wrapped), wrapped)
