import uuid
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeBasicInfo(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="basicInfo"
    )
    projectName = models.CharField(max_length=200, blank=True, null=True)
    district = models.CharField(max_length=200, blank=True, null=True)
    projectProgrammeCompiler = models.CharField(max_length=100, blank=True, null=True)
    personsInvolved = models.CharField(max_length=200, blank=True, null=True)
    inspector = models.CharField(max_length=100, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    strategyGoals = models.TextField(blank=True, null=True)
    projectSize = models.CharField(max_length=200, blank=True, null=True)
    risks = models.TextField(blank=True, null=True)
    studyAndPlanningNeeds = models.TextField(blank=True, null=True)
    planningAndImplementationFeasibility = models.TextField(blank=True, null=True)
    specialConsiderations = models.TextField(blank=True, null=True)
    otherConsiderations = models.TextField(blank=True, null=True)

