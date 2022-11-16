import uuid
from django.db import models
from django.utils.timezone import now


class ProjectType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField(max_length=200)


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    HKRprojectID = models.CharField(max_length=200, blank=True, null=True)
    type = models.ForeignKey(ProjectType, on_delete=models.DO_NOTHING)
    created_date = models.DateTimeField(auto_now_add=True, blank=True)
    updated_date = models.DateTimeField(auto_now=True, blank=True)
