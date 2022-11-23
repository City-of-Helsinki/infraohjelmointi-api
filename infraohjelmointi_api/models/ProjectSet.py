import uuid
from django.db import models
from django.utils.translation import gettext_lazy as lazy


class ProjectSet(models.Model):
    class ProjectPhaseChoices(models.TextChoices):
        PROPOSAL = "proposal", lazy("Proposal")
        DESIGN = "design", lazy("Design")
        PROGRAMMING = "ohjelmointi", lazy("Programming")
        DRAFT_INITIATION = "draftInitiation", lazy("DraftInitiation")
        DRAFT_APPROVAL = "draftApproval", lazy("DraftApproval")
        CONSTRUCTION_PLAN = "constructionPlan", lazy("ConstructionPlan")
        CONSTRUCTION_WAIT = "constructionWait", lazy("ConstructionWait")
        CONSTRUCTION = "construction", lazy("Construction")
        WARRANTY_PERIOD = "warrantyPeriod", lazy("WarrantyPeriod")
        COMPLETED = "completed", lazy("Completed")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=True, null=True)
    hkrId = models.IntegerField(blank=True, null=True)
    description = models.TextField(max_length=500, blank=True, null=True)
    responsiblePerson = models.ForeignKey(
        "Person", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    phase = models.CharField(
        max_length=16,
        choices=ProjectPhaseChoices.choices,
        default=ProjectPhaseChoices.PROPOSAL,
    )
    programmed = models.BooleanField(default=False)
    # finances = models.TextField(max_length=500, blank=True, null=True)

    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "id",
                    "hkrId",
                ],
                name="Unique together Constraint ProjectSet",
            )
        ]
