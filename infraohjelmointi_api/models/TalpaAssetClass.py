import uuid
from django.db import models


class TalpaAssetClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    componentClass = models.CharField(
        max_length=20, blank=False, null=False
    )  # Kom-luokka, e.g., "8103000", "8106100"
    account = models.CharField(max_length=20, blank=False, null=False)  # Tili, e.g., "103000", "106100"
    name = models.CharField(max_length=200, blank=False, null=False)  # e.g., "Maa- ja vesialueet"
    holdingPeriodYears = models.PositiveIntegerField(
        blank=True, null=True
    )  # Nullable, e.g., 5, 10, 15, 20, 30, 40
    hasHoldingPeriod = models.BooleanField(
        default=True
    )  # True if has holding period, False if "EP" (Ei Pitoaikaa)
    category = models.CharField(
        max_length=100, blank=True, null=True
    )  # "Aineelliset hyödykkeet" or "Kiinteät rakenteet ja laitteet"
    isActive = models.BooleanField(default=True)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["componentClass", "account"],
                name="Unique constraint TalpaAssetClass componentClass account",
            )
        ]
        ordering = ["componentClass"]

    def __str__(self):
        return f"{self.componentClass} - {self.name}"

