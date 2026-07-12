import uuid
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeTrafficPlanningCriteria(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="trafficPlanningCriteria"
    )
    pedestrianTraffic = models.TextField(blank=True, null=True)
    bicycleTraffic = models.TextField(blank=True, null=True)
    serviceAndPickupTraffic = models.TextField(blank=True, null=True)
    otherTraffic = models.TextField(blank=True, null=True)
    accessibility = models.TextField(blank=True, null=True)
    noiseManagement = models.TextField(blank=True, null=True)
    winterMaintenance = models.TextField(blank=True, null=True)