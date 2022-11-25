import uuid
from django.db import models
from .ProjectPhase import ProjectPhase
from django.utils.translation import gettext_lazy as lazy


class ProjectSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=True, null=True)
    hkrId = models.IntegerField(blank=True, null=True)
    description = models.TextField(max_length=500, blank=True, null=True)
    responsiblePerson = models.ForeignKey(
        "Person", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    phase = models.ForeignKey(
        ProjectPhase, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    programmed = models.BooleanField(default=False)
    # finances = models.TextField(max_length=500, blank=True, null=True)

    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "id",
                    "hkrId",
                ],
                name="Unique together Constraint ProjectSet",
            )
        ]
