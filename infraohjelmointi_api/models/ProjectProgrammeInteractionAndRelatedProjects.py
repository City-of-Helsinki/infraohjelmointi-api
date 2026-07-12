import uuid
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeInteractionAndRelatedProjects(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="interactionAndRelatedProjects"
    )
    maintenanceNeeds = models.TextField(blank=True)
    collaborationAndExperts = models.TextField(blank=True)
    interactionNotes = models.TextField(blank=True)

    history_fields = [
        "status",
        "maintenanceNeeds",
        "collaborationAndExperts",
        "interactionNotes",
        "_history_user",
    ]
