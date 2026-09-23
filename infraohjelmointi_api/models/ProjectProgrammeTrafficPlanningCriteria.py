import uuid
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeTrafficPlanningCriteria(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="trafficPlanningCriteria"
    )
    targetTrafficChanges = models.TextField(blank=True)
    pedestrianTraffic = models.TextField(blank=True)
    bicycleTraffic = models.TextField(blank=True)
    carTraffic = models.TextField(blank=True)
    serviceAndPickupTraffic = models.TextField(blank=True)
    otherTraffic = models.TextField(blank=True)
    accessibility = models.TextField(blank=True)
    noiseManagement = models.TextField(blank=True)
    winterMaintenance = models.TextField(blank=True)

    history_fields = [
        "targetTrafficChanges",
        "status",
        "pedestrianTraffic",
        "bicycleTraffic",
        "carTraffic",
        "serviceAndPickupTraffic",
        "otherTraffic",
        "accessibility",
        "noiseManagement",
        "winterMaintenance",
        "_history_user",
    ]
