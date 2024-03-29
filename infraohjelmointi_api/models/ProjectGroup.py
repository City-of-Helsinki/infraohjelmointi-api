import uuid
from django.db import models
from .ProjectLocation import ProjectLocation
from .ProjectClass import ProjectClass
from .ProjectDistrict import ProjectDistrict


class ProjectGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=False, null=False)
    location = models.ForeignKey(
        ProjectDistrict, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    locationRelation = models.ForeignKey(
        ProjectLocation, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    classRelation = models.ForeignKey(
        ProjectClass, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "name",
                    "location",
                    "locationRelation",
                    "classRelation",
                ],
                name="Unique together Constraint Project Group",
            )
        ]
        ordering = ["-id"]
