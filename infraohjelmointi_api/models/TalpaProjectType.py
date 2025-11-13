import uuid
from django.db import models


class TalpaProjectType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, blank=False, null=False)  # e.g., "8 03 01 01", can be alphanumeric like "8030101A"
    name = models.CharField(max_length=200, blank=False, null=False)  # e.g., "Katujen uudisrakentaminen"
    category = models.CharField(max_length=100, blank=True, null=True)  # e.g., "KADUT, LIIKENNEVÄYLÄT JA RADAT"
    priority = models.CharField(max_length=20, blank=True, null=True)  # "Normaali", "Korkea", "Ei käytössä", "Ei prioriteettia"
    description = models.TextField(blank=True, null=True)  # Detailed description from Excel
    isActive = models.BooleanField(default=True)  # Exclude obsolete entries
    notes = models.TextField(blank=True, null=True)  # Special notes like "EI UUSIA HANKKEITA V. 2022 JÄLKEEN!"
    validityYear = models.PositiveIntegerField(blank=True, null=True)  # For year-specific data
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                name="Unique constraint TalpaProjectType code",
            )
        ]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

