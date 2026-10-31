import datetime

from django.utils import timezone
from django_eventstream import models
from django_eventstream.storage import EVENT_TIMEOUT, DjangoModelStorage


class BulkTrimDjangoModelStorage(DjangoModelStorage):
    """DjangoModelStorage whose expiry trim is a single DELETE.

    The library trims on every ``send_event`` by deleting expired rows one at a
    time, 50 per batch, until none are left. After a quiet night that is one
    query per event from the previous day, run inside whichever user request
    sends the first event of the morning (~1400 queries / ~1 s locally).
    """

    def trim_event_log(self):
        cutoff = timezone.now() - datetime.timedelta(minutes=EVENT_TIMEOUT)
        models.Event.objects.filter(created__lt=cutoff).delete()
