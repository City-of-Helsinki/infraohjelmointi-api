import uuid
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from .ProjectProgrammeBase import ProjectProgrammeBase
from .ProjectProgramme import ProjectProgramme


class ProjectProgrammeTrafficPlanningCriteria(ProjectProgrammeBase):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project_programme = models.OneToOneField(
        ProjectProgramme, on_delete=models.CASCADE, related_name="trafficPlanningCriteria"
    )
    # IO-914: the section's "Liitetiedostot". Also cascades attachment rows (and,
    # via signals.py, their files) when the section is deleted.
    attachments = GenericRelation(
        "ProjectProgrammeAttachment",
        content_type_field="sectionType",
        object_id_field="sectionId",
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
