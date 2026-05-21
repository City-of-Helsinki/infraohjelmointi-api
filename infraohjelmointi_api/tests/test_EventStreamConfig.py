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
