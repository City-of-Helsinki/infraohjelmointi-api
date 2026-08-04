import uuid
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeBasicInfo(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="basicInfo"
    )
    projectName = models.CharField(max_length=200, blank=True)
    district = models.CharField(max_length=200, blank=True)
    projectProgrammeCompiler = models.CharField(max_length=100, blank=True)
    personsInvolved = models.CharField(max_length=200, blank=True)
    inspector = models.CharField(max_length=100, blank=True)
    summary = models.TextField(blank=True)
    strategyGoals = models.TextField(blank=True)
    costClass = models.TextField(blank=True)
    projectSize = models.CharField(max_length=200, blank=True)
    risks = models.TextField(blank=True)
    studyAndPlanningNeeds = models.TextField(blank=True)
    planningAndImplementationFeasibility = models.TextField(blank=True)
    specialConsiderations = models.TextField(blank=True)
    otherConsiderations = models.TextField(blank=True)

    history_fields = [
        "status",
        "projectName",
        "district",
        "projectProgrammeCompiler",
        "personsInvolved",
        "inspector",
        "summary",
        "strategyGoals",
        "costClass",
        "projectSize",
        "risks",
        "studyAndPlanningNeeds",
        "planningAndImplementationFeasibility",
        "specialConsiderations",
        "otherConsiderations",
        "_history_user",
    ]

