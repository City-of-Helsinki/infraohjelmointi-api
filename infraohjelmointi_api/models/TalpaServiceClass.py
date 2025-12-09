import uuid
from django.db import models


class TalpaServiceClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, blank=False, null=False)  # e.g., "4601", "4701", "3551", "5361"
    name = models.CharField(max_length=200, blank=False, null=False)  # e.g., "Kadut ja yleiset alueet"
    description = models.TextField(blank=True, null=True)  # Detailed description from Excel
    projectTypePrefix = models.CharField(
        max_length=10, blank=True, null=True
    )  # "2814I" or "2814E" - which project type prefix uses this service class
    isActive = models.BooleanField(default=True)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                name="Unique constraint TalpaServiceClass code",
            )
        ]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

