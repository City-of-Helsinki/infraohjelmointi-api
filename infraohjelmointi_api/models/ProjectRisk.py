import uuid
from django.db import models


class ProjectArea(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField(max_length=200, blank=False, null=False)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
