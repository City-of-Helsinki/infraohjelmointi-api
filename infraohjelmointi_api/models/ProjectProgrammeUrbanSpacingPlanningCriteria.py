import uuid
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeUrbanSpacingPlanningCriteria(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="urbanSpacingPlanningCriteria"
    )
    # IO-914: the section's "Liitetiedostot". Also cascades attachment rows (and,
    # via signals.py, their files) when the section is deleted.
    attachments = GenericRelation(
        "ProjectProgrammeAttachment",
        content_type_field="sectionType",
        object_id_field="sectionId",
    )
    targetUrbanAppearance = models.TextField(blank=True)
    surfaceMaterials = models.TextField(blank=True)
    structures = models.TextField(blank=True)
    technicalNetworksAndSystems = models.TextField(blank=True)
    lighting = models.TextField(blank=True)
    greenery = models.TextField(blank=True)
    lumoConsiderationAndProtection = models.TextField(blank=True)
    natureTypes = models.TextField(blank=True)

    equipmentAndFurnishings = models.TextField(blank=True)
    waters = models.TextField(blank=True)
    stormwaterManagement = models.TextField(blank=True)

    history_fields = [
        "status",
        "targetUrbanAppearance",
        "surfaceMaterials",
        "structures",
        "technicalNetworksAndSystems",
        "lighting",
        "greenery",
        "lumoConsiderationAndProtection",
        "natureTypes",
        "equipmentAndFurnishings",
        "waters",
        "stormwaterManagement",
        "_history_user",
    ]
