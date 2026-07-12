import uuid
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeDesignCriteria(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="designCriteria"
    )
    guidingZoningRegulations = models.TextField(blank=True)
    siteValuesProtectionAndSignificance = models.TextField(blank=True)
    relationshipToPublicAreaServices = models.TextField(blank=True)

    history_fields = [
        "status",
        "guidingZoningRegulations",
        "siteValuesProtectionAndSignificance",
        "relationshipToPublicAreaServices",
        "_history_user",
    ]
