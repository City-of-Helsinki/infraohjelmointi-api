import uuid
from django.db import models
from .HistoricalModel import HistoricalModel


class ProjectProgrammeBase(HistoricalModel):
    class Meta:
        abstract = True

    STATUS_CHOICES = [
        ("DRAFT", "DRAFT"),
        ("COMPLETE", "COMPLETE"),
    ]
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
    createdBy = models.ForeignKey(
        "User", on_delete=models.DO_NOTHING, blank=True, null=True, to_field="uuid", related_name="%(app_label)s_%(class)s_createdBy"
    )
    updatedBy = models.ForeignKey(
        "User", on_delete=models.DO_NOTHING, blank=True, null=True, to_field="uuid", related_name="%(app_label)s_%(class)s_updatedBy"
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, blank=False, null=False, default="DRAFT")

    history_fields = [
        "status",
        "_history_user",
    ]

    @property
    def _history_user(self):
        return self.updatedBy

    @_history_user.setter
    def _history_user(self, value):
        self.updatedBy = value

    @property
    def is_locked(self):
        """The project programme is locked if it's not in DRAFT status"""
        return self.status != "DRAFT"
