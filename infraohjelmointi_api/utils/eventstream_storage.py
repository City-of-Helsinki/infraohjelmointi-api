import datetime

from django.db.models import OuterRef, Subquery
from django.utils import timezone
from django_eventstream import models
from django_eventstream.storage import EVENT_TIMEOUT, DjangoModelStorage


class BulkTrimDjangoModelStorage(DjangoModelStorage):
    """DjangoModelStorage whose expiry trim is a single DELETE.

    The library trims on every ``send_event`` by deleting expired rows one at a
    time, 50 per batch, until none are left. After a quiet night that is one
    query per event from the previous day, run inside whichever user request
    sends the first event of the morning (~1400 queries / ~1 s locally).

    Each channel's newest expired event is kept. An open stream re-reads the
    table from the last event it got (``get_events``), and when that row is
    gone the library answers with a ``stream-reset`` and no events, which the
    UI ignores. After a quiet day that last event is older than the cutoff, so
    trimming it together with the rest would lose the next event whenever a
    stream has to re-read for it (a lost publish, a Redis reconnect).
    """

    def trim_event_log(self):
        cutoff = timezone.now() - datetime.timedelta(minutes=EVENT_TIMEOUT)
        newest_expired = (
            models.Event.objects.filter(channel=OuterRef("channel"), created__lt=cutoff)
            .order_by("-eid")
            .values("eid")[:1]
        )
        models.Event.objects.filter(created__lt=cutoff, eid__lt=Subquery(newest_expired)).delete()
