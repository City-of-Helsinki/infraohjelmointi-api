import uuid
from django.db import models


class TalpaProjectNumberRange(models.Model):
    PROJECT_TYPE_PREFIX_CHOICES = [
        ("2814I", "2814I - Infrastructure Investment"),
        ("2814E", "2814E - Pre-construction"),
    ]

    UNIT_CHOICES = [
        ("Tontit", "Tontit - Plots"),
        ("Mao", "Mao - Land Use"),
        ("Geo", "Geo - Geotechnical"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projectTypePrefix = models.CharField(
        max_length=10, choices=PROJECT_TYPE_PREFIX_CHOICES, blank=False, null=False
    )  # "2814I" or "2814E" - distinguishes SAP vs MAKE format
    budgetAccount = models.CharField(
        max_length=50, blank=True, null=True
    )  # e.g., "8 03 01 01", can be alphanumeric like "8030101A"
    budgetAccountNumber = models.CharField(
        max_length=50, blank=True, null=True
    )  # Talousarviokohdan numero, e.g., "2814100000"
    rangeStart = models.CharField(max_length=20, blank=False, null=False)  # e.g., "2814100003" or "2814E01000"
    rangeEnd = models.CharField(max_length=20, blank=False, null=False)  # e.g., "2814100300" or "2814E01599"
    majorDistrict = models.CharField(
        max_length=10, blank=True, null=True
    )  # Suurpiiri code, e.g., "01", "02"
    majorDistrictName = models.CharField(
        max_length=100, blank=True, null=True
    )  # Suurpiiri name, e.g., "Eteläinen", "Läntinen"
    area = models.CharField(max_length=100, blank=True, null=True)  # Alue, e.g., "011 Keskusta"
    unit = models.CharField(
        max_length=50, choices=UNIT_CHOICES, blank=True, null=True
    )  # For MAKE ranges: "Tontit", "Mao", "Geo"
    contactPerson = models.CharField(max_length=200, blank=True, null=True)  # For MAKE ranges
    contactEmail = models.EmailField(blank=True, null=True)  # For MAKE ranges
    transferNote = models.TextField(blank=True, null=True)  # Siirtohuomautus for SAP ranges
    notes = models.TextField(blank=True, null=True)  # Transfer notes, special instructions
    groupLabel = models.CharField(
        max_length=200, blank=True, null=True
    )  # Computed group label for UI dropdown grouping (e.g., "8 03 01 01 Katujen uudisrakentaminen")
    isActive = models.BooleanField(default=True)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        ordering = ["projectTypePrefix", "budgetAccount", "rangeStart"]

    def __str__(self):
        return f"{self.projectTypePrefix} - {self.rangeStart} to {self.rangeEnd}"

