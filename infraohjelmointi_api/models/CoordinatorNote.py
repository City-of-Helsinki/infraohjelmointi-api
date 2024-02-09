import uuid
import django.core.validators
from django.db import models
from django.core.exceptions import ValidationError
from overrides import override

class CoordinatorNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    coordinatorNote = models.TextField(blank=True, null=False, default="")
    year = models.PositiveIntegerField(validators=[
        django.core.validators.MinValueValidator(1900),
        django.core.validators.MaxValueValidator(3000),
    ])
    coordinatorClassName = models.CharField(max_length=150)
    coordinatorClass = models.ForeignKey("ProjectClass", on_delete=models.DO_NOTHING, null=True, blank=False)

    updatedBy = models.ForeignKey("User", on_delete=models.DO_NOTHING, null=True, blank=False, to_field="uuid")
    updatedByFirstName = models.CharField(max_length=50)
    updatedByLastName = models.CharField(max_length=50)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

