import uuid
from django.db import models


class ProjectHashTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField(max_length=100, unique=True)
    archived = models.BooleanField(default=False, null=False, blank=False)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
