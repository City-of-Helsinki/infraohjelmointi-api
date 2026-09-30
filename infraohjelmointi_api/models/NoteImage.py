import uuid
from django.db import models


class NoteImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.ForeignKey(
        "Note", on_delete=models.CASCADE, related_name="images", null=False, blank=False
    )
    file = models.FileField(upload_to="note_images/%Y/%m/", blank=False, null=False)
    fileName = models.CharField(max_length=255, blank=False, null=False)
    contentType = models.CharField(max_length=64, blank=False, null=False)
    size = models.PositiveIntegerField(null=False, default=0)
    order = models.PositiveIntegerField(null=False, default=0)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    uploadedBy = models.ForeignKey(
        "User",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        to_field="uuid",
        related_name="uploaded_note_images",
    )

    class Meta:
        ordering = ["order", "createdDate"]

    def __str__(self):
        return f"NoteImage {self.fileName} for note {self.note_id}"
