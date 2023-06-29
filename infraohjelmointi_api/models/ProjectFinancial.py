import uuid
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import date


class ProjectFinancial(models.Model):
    def currentYear():
        return date.today().year

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.PositiveIntegerField(
        blank=False,
        null=False,
        validators=[MinValueValidator(0), MaxValueValidator(3000)],
        default=currentYear,
    )
    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="finances",
    )
    value = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )

    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "project",
                    "year",
                ],
                name="Unique together Constraint Project Financial",
            )
        ]
