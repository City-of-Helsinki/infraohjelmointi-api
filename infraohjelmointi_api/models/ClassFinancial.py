import uuid
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import date
from django.db.models import CheckConstraint, Q, F, UniqueConstraint


class ClassFinancial(models.Model):
    def currentYear():
        return date.today().year

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    year = models.PositiveIntegerField(
        blank=False,
        null=False,
        validators=[MinValueValidator(0), MaxValueValidator(3000)],
        default=currentYear,
    )
    classRelation = models.ForeignKey(
        "ProjectClass",
        on_delete=models.CASCADE,
        blank=False,
        null=False,
        related_name="finances",
    )
    frameBudget = models.PositiveIntegerField(blank=True, null=True, default=0)
    budgetChange = models.PositiveIntegerField(blank=True, null=True, default=0)

    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=[
                    "classRelation",
                    "year",
                ],
                name="Unique together Constraint Class Financial",
            )
        ]
