import uuid
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeMaintenanceNeeds(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="maintenanceNeeds"
    )
    # IO-914: the section's "Liitetiedostot". Also cascades attachment rows (and,
    # via signals.py, their files) when the section is deleted.
    attachments = GenericRelation(
        "ProjectProgrammeAttachment",
        content_type_field="sectionType",
        object_id_field="sectionId",
    )
    maintenanceNeeds = models.TextField(blank=True)

    history_fields = [
        "status",
        "maintenanceNeeds",
        "_history_user",
    ]
