import uuid
from django.db import models
from .HistoricalModel import HistoricalModel


class Note(HistoricalModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.TextField(blank=True, null=False, default="")
    updatedBy = models.ForeignKey(
        "User", on_delete=models.DO_NOTHING, null=True, blank=False, to_field="uuid"
    )
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
    project = models.ForeignKey(
        "Project", on_delete=models.DO_NOTHING, null=False, blank=False
        #"Project", on_delete=models.CASCADE, null=False, blank=False
    )

    deleted = models.BooleanField(null=False, default=False)

    history_fields = ["content", "_history_user"]

    @property
    def _history_user(self):
        return self.updatedBy

    @_history_user.setter
    def _history_user(self, value):
        self.updatedBy = value
