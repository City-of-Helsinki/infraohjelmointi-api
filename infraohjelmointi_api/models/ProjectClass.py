import uuid
from django.db import models


class ProjectClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="childClass",
    )
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
    path = models.CharField(max_length=300, blank=True, null=True)
    relatedTo = models.OneToOneField(
        "self",
        on_delete=models.DO_NOTHING,
        related_name="coordinatorClass",
        blank=True,
        null=True,
    )
    relatedLocation = models.OneToOneField(
        "ProjectLocation",
        on_delete=models.DO_NOTHING,
        related_name="relatedCoordinatorClass",
        blank=True,
        null=True,
    )
    forCoordinatorOnly = models.BooleanField(default=False)
