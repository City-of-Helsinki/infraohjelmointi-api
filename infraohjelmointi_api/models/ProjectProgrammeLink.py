import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class ProjectProgrammeLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contentType = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    objectId = models.UUIDField()
    sectionObject = GenericForeignKey("contentType", "objectId")
    value = models.URLField()
    createdDate = models.DateTimeField(auto_now_add=True)
    updatedDate = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["createdDate"]
        indexes = [
            models.Index(fields=["contentType", "objectId"]),
        ]
