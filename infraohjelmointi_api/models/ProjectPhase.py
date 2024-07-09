import uuid
from django.db import models


class ProjectPhase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField(max_length=30)
    index = models.PositiveIntegerField(default=0, blank=False, null=False)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["value"],
                name="Unique constraint ProjectPhase",
            )
        ]
