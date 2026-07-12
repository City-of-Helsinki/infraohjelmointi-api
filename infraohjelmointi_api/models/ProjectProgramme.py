import uuid
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .Project import Project


class ProjectProgramme(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="projectProgramme"
    )
    briefProjectProgramme = models.BooleanField(default=True, blank=True, null=True)
