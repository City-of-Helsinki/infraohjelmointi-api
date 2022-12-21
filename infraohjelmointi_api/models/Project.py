import random
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as lazy
from .ProjectSet import ProjectSet
from .ProjectArea import ProjectArea
from .BudgetItem import BudgetItem
from .Person import Person
from .ProjectType import ProjectType
from .ProjectPhase import ProjectPhase
from .ProjectPriority import ProjectPriority
from .ConstructionPhaseDetail import ConstructionPhaseDetail
from .ProjectCategory import ProjectCategory
from .ProjectRisk import ProjectRisk
from .ProjectQualityLevel import ProjectQualityLevel
from .ProjectBuildPhase import ProjectBuildPhase
from .PlanningPhase import PlanningPhase
from django.core.validators import MaxValueValidator, MinValueValidator
from overrides import override


class Project(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    siteId = models.ForeignKey(
        BudgetItem, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    category = models.ForeignKey(
        ProjectCategory, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    effectHousing = models.BooleanField(default=False)
    hkrId = models.PositiveBigIntegerField(blank=True, null=True)
    entityName = models.CharField(max_length=30, blank=True, null=True)
    sapProject = models.CharField(max_length=100, blank=True, null=True)
    sapNetwork = models.JSONField(blank=True, null=True)
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
    address = models.CharField(max_length=250, blank=True, null=True)
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
    phase = models.ForeignKey(
        ProjectPhase, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    favPersons = models.ManyToManyField(
        Person, related_name="favourite", null=True, blank=True
    )
    programmed = models.BooleanField(default=False)
    constructionPhaseDetail = models.ForeignKey(
        ConstructionPhaseDetail, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    planningStartYear = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(3000)],
        default=0,
    )
    constructionEndYear = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(3000)],
        default=0,
    )
    projectWorkQuantity = models.PositiveIntegerField(blank=True, null=True, default=0)
    projectlevelOfQuality = models.ForeignKey(
        ProjectQualityLevel, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    projectCostForecast = models.PositiveIntegerField(blank=True, null=True, default=0)

    planningCostForecast = models.PositiveIntegerField(blank=True, null=True, default=0)
    planningWorkQuantity = models.PositiveIntegerField(blank=True, null=True, default=0)
    planningPhase = models.ForeignKey(
        PlanningPhase, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    estConstructionCost = models.PositiveIntegerField(blank=True, null=True, default=0)

    buildPhase = models.ForeignKey(
        ProjectBuildPhase, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    estPlanningStart = models.DateField(blank=True, null=True)
    estPlanningEnd = models.DateField(blank=True, null=True)
    estConstructionStart = models.DateField(blank=True, null=True)
    estConstructionEnd = models.DateField(blank=True, null=True)
    presenceStart = models.DateField(blank=True, null=True)
    presenceEnd = models.DateField(blank=True, null=True)
    visibilityStart = models.DateField(blank=True, null=True)
    visibilityEnd = models.DateField(blank=True, null=True)
    louhi = models.BooleanField(default=False)
    gravel = models.BooleanField(default=False)

    perfAmount = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    unitCost = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    costForecast = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    neighborhood = models.CharField(max_length=200, blank=True, null=True)
    comittedCost = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    tiedCurrYear = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    realizedCost = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    spentCost = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    riskAssessment = models.ForeignKey(
        ProjectRisk, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    priority = models.ForeignKey(
        ProjectPriority, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    locked = models.BooleanField(default=False)
    comments = models.CharField(max_length=200, blank=True, null=True)

    # commented fields left out due to translation confusions
    budgetForecast1CurrentYear = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    budgetForecast2CurrentYear = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    budgetForecast3CurrentYear = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    budgetForecast4CurrentYear = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    budgetProposalCurrentYearPlus1 = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    budgetProposalCurrentYearPlus2 = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    preliminaryCurrentYearPlus3 = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    preliminaryCurrentYearPlus4 = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    preliminaryCurrentYearPlus5 = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    preliminaryCurrentYearPlus6 = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    preliminaryCurrentYearPlus7 = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    preliminaryCurrentYearPlus8 = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    preliminaryCurrentYearPlus9 = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    preliminaryCurrentYearPlus10 = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )

    delays = models.CharField(max_length=200, blank=True, null=True)
    hashTags = models.JSONField(blank=True, null=True)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    def projectReadiness(self):
        # some calculation based on cost and stuff
        # returns percentage of readiness random.randint(0, 100)
        return 95

    @override
    def save(self, *args, **kwargs):
        self.full_clean()
        super(Project, self).save(*args, **kwargs)

    @override
    def clean(self):
        """
        Custom validation
        Cleaning charfields: Stripping leading, trailing and excess in between spaces.
        """

        self.name = " ".join(self.name.split())
        self.description = " ".join(self.description.split())
        if self.address:
            self.address = " ".join(self.address.split())
        if self.entityName:
            self.entityName = " ".join(self.entityName.split())
        if self.neighborhood:
            self.neighborhood = " ".join(self.neighborhood.split())
        if self.comments:
            self.comments = " ".join(self.comments.split())
        if self.delays:
            self.delays = " ".join(self.delays.split())

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
        ordering = ["-id"]
