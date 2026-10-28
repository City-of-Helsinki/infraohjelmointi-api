"""Tests that pin django-eventstream's runtime configuration.

These tests are intentionally tiny — they exist to lock in the choice we
documented in IO-890 so that a future settings refactor, dependency bump, or
copy-paste accident doesn't silently regress us back to in-memory storage
(which would resurrect the IO-725 / IO-890 cross-pod event-loss bug).
"""

from django.test import TestCase

from django_eventstream.storage import DjangoModelStorage
from django_eventstream.utils import get_storage


class EventStreamStorageConfigTest(TestCase):
    """django-eventstream must use a persisted storage backend.

    IO-890: ``django-eventstream==4.5.x`` has no Redis backend; persisted
    storage is the only mechanism by which an SSE client reconnecting to a
    different pod can replay events fired on another pod (via the standard
    ``Last-Event-ID`` header). Without storage every event lives only in the
    in-process listener queue of the pod that handled the write.
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
            "Storage backend must be DjangoModelStorage. EVENTSTREAM_REDIS is "
            "silently ignored by django-eventstream 4.5.x.",
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

        self.assertEqual(Event.objects.count(), 20)
