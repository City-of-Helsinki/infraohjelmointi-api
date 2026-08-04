import uuid
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeMaintenanceNeeds(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="maintenanceNeeds"
    )
    maintenanceNeeds = models.TextField(blank=True)

    history_fields = [
        "status",
        "maintenanceNeeds",
        "_history_user",
    ]
