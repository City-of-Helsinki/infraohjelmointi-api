import uuid
from django.db import models


class ConstructionHandoverAttachment(models.Model):
    """A file attached to a construction handover (IO-857).

    Field names follow the ticket spec. Note that this deliberately mirrors
    NoteImage (IO-812) without sharing a base model: the two have different owners
    and different allowed content types, and the reusable part - validation - lives
    in utils/upload_validation.py instead. If IO-914 adds a third variant for
    hankeohjelma it is worth revisiting whether an abstract base pays for itself.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    handover = models.ForeignKey(
        "ConstructionHandover",
        on_delete=models.CASCADE,
        related_name="attachments",
        null=False,
        blank=False,
    )
    file = models.FileField(upload_to="handover_attachments/%Y/%m/", blank=False, null=False)
    originalName = models.CharField(max_length=255, blank=False, null=False)
    contentType = models.CharField(max_length=100, blank=False, null=False)
    size = models.PositiveIntegerField(null=False, default=0)
    uploadedBy = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        to_field="uuid",
        related_name="uploaded_handover_attachments",
    )
    uploadedDate = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        app_label = "infraohjelmointi_api"
        ordering = ["uploadedDate"]

    def __str__(self):
        return f"ConstructionHandoverAttachment {self.originalName} for handover {self.handover_id}"
