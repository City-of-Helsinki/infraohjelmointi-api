import uuid
from datetime import datetime
from django.db import models

from .ProjectGroup import ProjectGroup
from .Project import Project


class SapCurrentYear(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_group = models.ForeignKey(
        ProjectGroup, on_delete=models.SET_NULL, null=True, blank=True
    )
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL, null=True, blank=True
    )
    year = models.IntegerField(null=None)
    sap_id = models.CharField(null=None, max_length=30)
    project_task_costs = models.DecimalField(
        null=None, default=0.000, decimal_places=3, max_digits=20
    )
    project_task_commitments = models.DecimalField(
        null=None, default=0.000, decimal_places=3, max_digits=20
    )
    production_task_costs = models.DecimalField(
        null=None, default=0.000, decimal_places=3, max_digits=20
    )
    production_task_commitments = models.DecimalField(
        null=None, default=0.000, decimal_places=3, max_digits=20
    )
    group_combined_commitments = models.DecimalField(
        null=None, default=0.000, decimal_places=3, max_digits=20
    )
    group_combined_costs = models.DecimalField(
        null=None, default=0.000, decimal_places=3, max_digits=20
    )
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
