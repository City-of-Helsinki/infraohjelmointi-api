import uuid
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeUrbanSpacingPlanningCriteria(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="urbanSpacingPlanningCriteria"
    )
    targetUrbanAppearance = models.TextField(blank=True, null=True)
    surfaceMaterials = models.TextField(blank=True, null=True)
    structures = models.TextField(blank=True, null=True)
    technicalNetworksAndSystems = models.TextField(blank=True, null=True)
    lighting = models.TextField(blank=True, null=True)
    greenery = models.TextField(blank=True, null=True)
    lumoConsiderationAndProtection = models.TextField(blank=True, null=True)
    natureTypes = models.TextField(blank=True, null=True)

    equipmentAndFurnishings = models.TextField(blank=True, null=True)
    waters = models.TextField(blank=True, null=True)
    stormwaterManagement = models.TextField(blank=True, null=True)