import uuid
from django.db import models

from .ProjectClass import ProjectClass


class ProjectLocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="childLocation",
    )
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
    path = models.CharField(max_length=300, blank=True, null=True)
    parentClass = models.ForeignKey(
        ProjectClass, blank=True, null=True, on_delete=models.DO_NOTHING
    )
    relatedTo = models.ForeignKey(
        "self", blank=True, null=True, on_delete=models.DO_NOTHING
    )
    forCoordinatorOnly = models.BooleanField(default=False)
