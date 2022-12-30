import uuid
from django.db import models
from .Person import Person
from simple_history.models import HistoricalRecords


class Note(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField(blank=True, null=False, default="")
    updatedBy = models.ForeignKey(
        "Person", on_delete=models.DO_NOTHING, null=False, blank=False
    )
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
    project = models.ForeignKey(
        "Project", on_delete=models.DO_NOTHING, null=False, blank=False
    )
    history = HistoricalRecords(user_model=Person)
    deleted = models.BooleanField(null=False, default=False)

    def save_without_historical_record(self, *args, **kwargs):
        self.skip_history_when_saving = True
        try:
            ret = self.save(*args, **kwargs)
        finally:
            del self.skip_history_when_saving
        return ret

    @property
    def _history_user(self):
        return self.updatedBy

    @_history_user.setter
    def _history_user(self, value):
        self.updatedBy = value
