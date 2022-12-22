import uuid
from django.db import models


class ProjectClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=30)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
