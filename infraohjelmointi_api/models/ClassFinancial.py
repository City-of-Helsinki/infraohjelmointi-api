import uuid
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import date
from django.db.models import UniqueConstraint
from django.core.exceptions import ValidationError
from overrides import override


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
    budgetChange = models.IntegerField(blank=True, null=True, default=0)
    forFrameView = models.BooleanField(blank=False, default=False)

    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=[
                    "classRelation",
                    "year",
                    "forFrameView"
                ],
                name="Unique together Constraint Class Financial",
            )
        ]

    # Overriding clean() method to validate classRelation
    @override
    def clean(self):
        if self.classRelation.forCoordinatorOnly != True:
            raise ValidationError(
                {"classRelation": "classRelation can only point to a coordinator class"}
            )

    # Overriding save method to ensure the clean() method is called before save
    @override
    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
