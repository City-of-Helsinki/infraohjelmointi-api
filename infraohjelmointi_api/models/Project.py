import random
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as lazy
from .ProjectSet import ProjectSet
from .ProjectArea import ProjectArea
from .BudgetItem import BudgetItem
from .Person import Person
from .ProjectType import ProjectType


class Project(models.Model):
    class ProjectPhaseChoices(models.TextChoices):
        PROPOSAL = "proposal", lazy("Proposal")
        DESIGN = "design", lazy("Design")
        PROGRAMMING = "programming", lazy("Programming")
        DRAFT_INITIATION = "draftInitiation", lazy("DraftInitiation")
        DRAFT_APPROVAL = "draftApproval", lazy("DraftApproval")
        CONSTRUCTION_PLAN = "constructionPlan", lazy("ConstructionPlan")
        CONSTRUCTION_WAIT = "constructionWait", lazy("ConstructionWait")
        CONSTRUCTION = "construction", lazy("Construction")
        WARRANTY_PERIOD = "warrantyPeriod", lazy("WarrantyPeriod")
        COMPLETED = "completed", lazy("Completed")

    class PriorityChoices(models.TextChoices):
        LOW = "low", lazy("Low")
        MEDIUM = "medium", lazy("Medium")
        HIGH = "high", lazy("High")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    siteId = models.ForeignKey(
        BudgetItem, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    hkrId = models.UUIDField(blank=True, null=True)
    entityName = models.CharField(max_length=30, blank=True, null=True)
    sapProject = models.UUIDField(blank=True, null=True)
    sapNetwork = models.UUIDField(blank=True, null=True)
    projectSet = models.ForeignKey(
        ProjectSet, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    area = models.ForeignKey(
        ProjectArea, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    type = models.ForeignKey(
        ProjectType, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(max_length=40, blank=False, null=False)
    personPlanning = models.ForeignKey(
        Person,
        related_name="planning",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
    )
    personProgramming = models.ForeignKey(
        Person,
        related_name="programming",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
    )
    personConstruction = models.ForeignKey(
        Person,
        related_name="construction",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
    )
    phase = models.CharField(
        max_length=16,
        choices=ProjectPhaseChoices.choices,
        default=ProjectPhaseChoices.PROPOSAL,
    )
    favPersons = models.ManyToManyField(
        Person, related_name="favourite", null=True, blank=True
    )
    programmed = models.BooleanField(default=False)
    constructionPhaseDetail = models.TextField(max_length=500, blank=True, null=True)
    estPlanningStartYear = models.IntegerField(blank=True, null=True)
    estDesignEndYear = models.IntegerField(blank=True, null=True)
    estDesignStartDate = models.DateField(blank=True, null=True)
    estDesignEndDate = models.DateField(blank=True, null=True)
    contractPrepStartDate = models.DateField(blank=True, null=True)
    contractPrepEndDate = models.DateField(blank=True, null=True)
    warrantyStartDate = models.DateField(blank=True, null=True)
    warrantyExpireDate = models.DateField(blank=True, null=True)
    perfAmount = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    unitCost = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    costForecast = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    neighborhood = models.CharField(max_length=200, blank=True, null=True)
    comittedCost = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    tiedCurrYear = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    realizedCost = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    spentCost = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    riskAssess = models.CharField(max_length=200, blank=True, null=True)
    priority = models.CharField(
        max_length=6,
        choices=PriorityChoices.choices,
        default=PriorityChoices.LOW,
    )
    locked = models.BooleanField(default=False)
    comments = models.CharField(max_length=200, blank=True, null=True)

    # commented fields left out due to translation confusions
    # Hankkeen lisätyöt (sapista)
    # TaEnnuste1KuluvaVuosi
    # TaEnnuste2KuluvaVuosi
    # TaEnnuste3KuluvaVuosi
    # TaEnnuste4KuluvaVuosi
    # TaeKuluvaVuosiPlus1
    # TaeKuluvaVuosiPlus2
    # AlustavaKuluvaVuosiPlus3
    # AlustavaKuluvaVuosiPlus4
    # AlustavaKuluvaVuosiPlus5
    # AlustavaKuluvaVuosiPlus6
    # AlustavaKuluvaVuosiPlus7
    # AlustavaKuluvaVuosiPlus8
    # AlustavaKuluvaVuosiPlus9
    # AlustavaKuluvaVuosiPlus10

    delays = models.CharField(max_length=200, blank=True, null=True)

    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    def projectReadiness(self):
        # some calculation based on cost and stuff
        # returns percentage of readiness random.randint(0, 100)
        return 95

    # Rediness % to be calculated

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "id",
                    "hkrId",
                    "sapProject",
                    "sapNetwork",
                    "projectSet",
                ],
                name="Unique together Constraint Project",
            )
        ]
