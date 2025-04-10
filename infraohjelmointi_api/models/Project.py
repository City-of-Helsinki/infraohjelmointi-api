import random
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as lazy

from .ProjectLocation import ProjectLocation
from .ProjectDistrict import ProjectDistrict
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
from .ConstructionPhase import ConstructionPhase
from .PlanningPhase import PlanningPhase
from .ProjectClass import ProjectClass
from .ResponsibleZone import ResponsibleZone
from .ProjectHashTag import ProjectHashTag
from .ProjectGroup import ProjectGroup
from django.core.validators import MaxValueValidator, MinValueValidator
from overrides import override


class Project(models.Model):
    def get_default_projectPhase():
        try:
            return ProjectPhase.objects.get(value="proposal")
        except ProjectPhase.DoesNotExist:
            return None

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    siteId = models.ForeignKey(
        BudgetItem, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    category = models.ForeignKey(
        ProjectCategory, on_delete=models.DO_NOTHING, null=True, blank=True
    )

    projectClass = models.ForeignKey(
        ProjectClass, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    projectLocation = models.ForeignKey(
        ProjectLocation, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    projectDistrict = models.ForeignKey(
        ProjectDistrict, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    projectGroup = models.ForeignKey(
        ProjectGroup, on_delete=models.SET_NULL, null=True, blank=True
    )
    effectHousing = models.BooleanField(default=False)
    hkrId = models.PositiveBigIntegerField(blank=True, null=True)
    entityName = models.CharField(max_length=256, blank=True, null=True)
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
    otherPersons = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(max_length=1000, blank=False, null=False)
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
        ProjectPhase,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        default=get_default_projectPhase,
    )
    favPersons = models.ManyToManyField(
        Person, related_name="favourite", blank=True
    )
    programmed = models.BooleanField(default=False)
    constructionPhaseDetail = models.ForeignKey(
        ConstructionPhaseDetail, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    planningStartYear = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(3000)],
        default=None,
    )
    constructionEndYear = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(3000)],
        default=None,
    )
    budgetOverrunYear = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(3000)],
        default=None,
    )
    budgetOverrunAmount = models.PositiveIntegerField(blank=True, null=True, default=0)
    projectWorkQuantity = models.PositiveIntegerField(blank=True, null=True, default=0)
    projectQualityLevel = models.ForeignKey(
        ProjectQualityLevel, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    projectCostForecast = models.PositiveIntegerField(blank=True, null=True, default=0)

    planningCostForecast = models.PositiveIntegerField(blank=True, null=True, default=0)
    planningWorkQuantity = models.PositiveIntegerField(blank=True, null=True, default=0)
    planningPhase = models.ForeignKey(
        PlanningPhase, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    budgetGroupPercentage = models.PositiveIntegerField(
        blank=True,
        null=True,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )
    constructionCostForecast = models.PositiveIntegerField(
        blank=True, null=True, default=0
    )
    constructionPhase = models.ForeignKey(
        ConstructionPhase, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    constructionWorkQuantity = models.PositiveIntegerField(
        blank=True, null=True, default=0
    )
    budget = models.PositiveIntegerField(blank=True, null=True, default=0)
    estPlanningStart = models.DateField(blank=True, null=True)
    estPlanningEnd = models.DateField(blank=True, null=True)
    estConstructionStart = models.DateField(blank=True, null=True)
    estConstructionEnd = models.DateField(blank=True, null=True)
    estWarrantyPhaseStart = models.DateField(blank=True, null=True)
    estWarrantyPhaseEnd = models.DateField(blank=True, null=True)
    frameEstPlanningStart = models.DateField(blank=True, null=True)
    frameEstPlanningEnd = models.DateField(blank=True, null=True)
    frameEstConstructionStart = models.DateField(blank=True, null=True)
    frameEstConstructionEnd = models.DateField(blank=True, null=True)
    frameEstWarrantyPhaseStart = models.DateField(blank=True, null=True)
    frameEstWarrantyPhaseEnd = models.DateField(blank=True, null=True)

    presenceStart = models.DateField(blank=True, null=True)
    presenceEnd = models.DateField(blank=True, null=True)
    visibilityStart = models.DateField(blank=True, null=True)
    visibilityEnd = models.DateField(blank=True, null=True)
    louhi = models.BooleanField(default=False)
    gravel = models.BooleanField(default=False)

    masterPlanAreaNumber = models.TextField(max_length=20, blank=True, null=True)
    trafficPlanNumber = models.TextField(max_length=20, blank=True, null=True)
    bridgeNumber = models.TextField(max_length=20, blank=True, null=True)

    perfAmount = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    unitCost = models.DecimalField(
        max_digits=20, decimal_places=2, default=0.0, blank=True, null=True
    )
    costForecast = models.PositiveIntegerField(
        default=0, blank=True, null=True
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
    comments = models.CharField(max_length=200, blank=True, null=True)

    responsibleZone = models.ForeignKey(
        ResponsibleZone, on_delete=models.DO_NOTHING, null=True, blank=True
    )
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
    projectProgram = models.TextField(max_length=15000, blank=True, null=True)

    delays = models.CharField(max_length=200, blank=True, null=True)
    hashTags = models.ManyToManyField(
        ProjectHashTag, related_name="relatedProject", blank=True
    )
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)

    def projectReadiness(self) -> int:
        # TODO: implement the calculation logic after we get SAP connection
        # Should be money spent (from SAP) divided by project budget
        # returns 95% now cause we don't have the SAP connection yet
        return 95

    def _strip_whitespaces(self, inputString: str) -> str:
        return "\n".join(" ".join(line.split()) for line in inputString.split("\n"))

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

        self.name = self._strip_whitespaces(self.name)
        self.description = self._strip_whitespaces(self.description)
        if self.address:
            self.address = self._strip_whitespaces(self.address)
        if self.entityName:
            self.entityName = self._strip_whitespaces(self.entityName)
        if self.neighborhood:
            self.neighborhood = self._strip_whitespaces(self.neighborhood)
        if self.comments:
            self.comments = self._strip_whitespaces(self.comments)
        if self.delays:
            self.delays = self._strip_whitespaces(self.delays)
        if self.otherPersons:
            self.otherPersons = self._strip_whitespaces(self.otherPersons)

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
