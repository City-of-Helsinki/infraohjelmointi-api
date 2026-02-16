import uuid
from django.db import models


class ProjectPhaseDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField(max_length=100)
    projectPhase = models.ForeignKey(
        "ProjectPhase", on_delete=models.CASCADE, related_name="phaseDetails"
    )
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    def __str__(self):
        return self.value
