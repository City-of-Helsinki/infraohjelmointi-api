"""Tests that pin django-eventstream's runtime configuration.

These tests are intentionally tiny — they exist to lock in the choice we
documented in IO-890 so that a future settings refactor, dependency bump, or
copy-paste accident doesn't silently regress us back to in-memory storage
(which would resurrect the IO-725 / IO-890 cross-pod event-loss bug).
"""

from unittest.mock import patch

from django.test import TestCase

from django_eventstream.storage import DjangoModelStorage
from django_eventstream.utils import get_storage

from infraohjelmointi_api.utils.eventstream_storage import BulkTrimDjangoModelStorage


class EventStreamStorageConfigTest(TestCase):
    """django-eventstream must use a persisted storage backend.

    IO-890: Redis pub/sub carries events live between processes, but the
    stored events are what a reconnecting client replays (via the standard
    ``Last-Event-ID`` header) and what open streams re-read after a Redis
    reconnect (utils/eventstream_setup.py). Without storage, anything sent
    while a browser or a subscriber was disconnected would be lost.
    """

    def test_storage_is_django_model_storage(self):
        storage = get_storage()
        self.assertIsNotNone(
            storage,
            "EVENTSTREAM_STORAGE_CLASS must be set (IO-890); without it, "
            "django-eventstream falls back to in-memory storage and SSE "
            "events do not survive a client reconnect or reach other pods.",
        )
        self.assertIsInstance(
            storage,
            DjangoModelStorage,
            "Storage backend must be DjangoModelStorage: the Redis channel only "
            "carries live events, it keeps nothing for replay.",
        )


class EventStreamTrimTest(TestCase):
    """Expired events are trimmed with one DELETE, not one query per row."""

    def test_trim_deletes_expired_events_in_one_query(self):
        import datetime

        from django.utils import timezone
        from django_eventstream.models import Event

        events = [Event.objects.create(channel="finance", type="t", data="{}", eid=i) for i in range(1, 121)]
        Event.objects.filter(id__in=[e.id for e in events[:100]]).update(
            created=timezone.now() - datetime.timedelta(days=2)
        )

        with self.assertNumQueries(1):
            get_storage().trim_event_log()

        # The 20 fresh events, and the newest expired one (see the next test).
        self.assertEqual(sorted(Event.objects.values_list("eid", flat=True)), list(range(100, 121)))

    def test_a_stream_can_reread_from_its_last_event_after_a_quiet_day(self):
        """The first event after a quiet day must not trim the event a stream
        re-reads from: without that row the library resets the stream and the
        new event is never delivered."""
        import datetime

        from django.utils import timezone
        from django_eventstream.models import Event

        storage = get_storage()
        last_seen = storage.append_event("finance", "yesterday", {})
        Event.objects.filter(channel="finance").update(created=timezone.now() - datetime.timedelta(days=2))

        storage.append_event("finance", "this-morning", {})

        self.assertEqual([e.type for e in storage.get_events("finance", int(last_seen.id))], ["this-morning"])

    def test_sending_an_event_runs_the_bulk_trim(self):
        """Guards the override against the library renaming or dropping its trim hook."""
        import datetime

        from django.utils import timezone
        from django_eventstream.models import Event

        old = Event.objects.create(channel="expired", type="t", data="{}", eid=1)
        Event.objects.create(channel="expired", type="t", data="{}", eid=2)
        Event.objects.filter(channel="expired").update(created=timezone.now() - datetime.timedelta(days=2))

        with patch.object(
            BulkTrimDjangoModelStorage, "trim_event_log", autospec=True,
            side_effect=BulkTrimDjangoModelStorage.trim_event_log,
        ) as trim:
            get_storage().append_event("finance", "t", {})

        trim.assert_called_once()
        self.assertFalse(Event.objects.filter(id=old.id).exists())
