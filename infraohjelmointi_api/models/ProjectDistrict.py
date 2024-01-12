import uuid
from django.db import models


class ProjectDistrict(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=False, null=False)
    level = models.CharField(max_length=200, blank=False, null=False)
    path = models.CharField(max_length=300, blank=False, null=False)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="childClass",
    )
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
