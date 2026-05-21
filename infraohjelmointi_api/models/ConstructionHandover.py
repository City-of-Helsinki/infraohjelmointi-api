import uuid
from django.db import models
from .HistoricalModel import HistoricalModel


class ConstructionHandover(HistoricalModel):
    STATUS_CHOICES = [
        ("DRAFT", "DRAFT"),
        ("SUBMITTED_TO_PROGRAMMER", "SUBMITTED_TO_PROGRAMMER"),
        ("SUBMITTED_TO_CONSTRUCTION", "SUBMITTED_TO_CONSTRUCTION"),
        ("PROJECT_MANAGER_NAMED", "PROJECT_MANAGER_NAMED"),
        ("MOVED_TO_CONSTRUCTION_PREPARATION", "MOVED_TO_CONSTRUCTION_PREPARATION"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        "Project", on_delete=models.CASCADE, null=False, blank=False
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, blank=False, null=False, default="DRAFT")
    name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    constructionProcurementMethod = models.ForeignKey(
        "ConstructionProcurementMethod", on_delete=models.DO_NOTHING, null=True, blank=True
    )
    constructionStart = models.DateField(blank=True, null=True)
    constructionEnd = models.DateField(blank=True, null=True)
    otherTimelineNotes = models.TextField(blank=True, null=True)
    totalCost = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    personPlanning = models.ForeignKey(
        "Person", related_name="handovers_planning", on_delete=models.DO_NOTHING, null=True, blank=True
    )
    personFinancing = models.ForeignKey(
        "ProjectProgrammer", related_name="handovers_financing", on_delete=models.DO_NOTHING, null=True, blank=True
    )
    linkDesignDrawings = models.URLField(max_length=500, blank=True, null=True)
    linkCostAllocation = models.URLField(max_length=500, blank=True, null=True)
    linkContractBoundaries = models.URLField(max_length=500, blank=True, null=True)
    constructionProjectManager = models.ForeignKey(
        "Person", related_name="handovers_pm", on_delete=models.DO_NOTHING, null=True, blank=True
    )
    previousProjectPhase = models.ForeignKey(
        "ProjectPhase", related_name="handovers_previous_phase", on_delete=models.DO_NOTHING, null=True, blank=True
    )

    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
    createdBy = models.ForeignKey(
        "User", on_delete=models.DO_NOTHING, blank=True, null=True, to_field="uuid", related_name="constructionhandover_createdBy"
    )
    updatedBy = models.ForeignKey(
        "User", on_delete=models.DO_NOTHING, blank=True, null=True, to_field="uuid", related_name="constructionhandover_updatedBy"
    )

    history_fields = [
        "status", "name", "description", "constructionProcurementMethod", "constructionStart",
        "constructionEnd", "otherTimelineNotes", "totalCost", "personPlanning", "personFinancing",
        "linkDesignDrawings", "linkCostAllocation", "linkContractBoundaries", "_history_user",
        "constructionProjectManager", "previousProjectPhase"
    ]

    @property
    def _history_user(self):
        return self.updatedBy

    @_history_user.setter
    def _history_user(self, value):
        self.updatedBy = value
