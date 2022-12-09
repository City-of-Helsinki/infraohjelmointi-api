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
from overrides import override


class Project(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    siteId = models.ForeignKey(
        BudgetItem, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    hkrId = models.IntegerField(blank=True, null=True)
    entityName = models.CharField(max_length=30, blank=True, null=True)
    sapProject = models.IntegerField(blank=True, null=True)
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
    priority = models.ForeignKey(
        ProjectPriority, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    locked = models.BooleanField(default=False)
    comments = models.CharField(max_length=200, blank=True, null=True)

    # commented fields left out due to translation confusions
    budgetForecast1CurrentYear = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    budgetForecast2CurrentYear = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    budgetForecast3CurrentYear = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    budgetForecast4CurrentYear = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    budgetProposalCurrentYearPlus1 = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    budgetProposalCurrentYearPlus2 = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    preliminaryCurrentYearPlus3 = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    preliminaryCurrentYearPlus4 = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    preliminaryCurrentYearPlus5 = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    preliminaryCurrentYearPlus6 = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    preliminaryCurrentYearPlus7 = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    preliminaryCurrentYearPlus8 = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    preliminaryCurrentYearPlus9 = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
    )
    preliminaryCurrentYearPlus10 = models.DecimalField(
        max_digits=20, decimal_places=2, blank=True, null=True
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
        Cleaning charfields: Stripping spaces and Capitalization
        """

        self.name = " ".join(self.name.split()).capitalize()
        self.description = " ".join(self.description.split()).capitalize()
        if self.address:
            self.address = " ".join(self.address.split()).capitalize()
        if self.entityName:
            self.entityName = " ".join(self.entityName.split()).capitalize()
        if self.neighborhood:
            self.neighborhood = " ".join(self.neighborhood.split()).capitalize()
        if self.riskAssess:
            self.riskAssess = " ".join(self.riskAssess.split()).capitalize()
        if self.comments:
            self.comments = " ".join(self.comments.split()).capitalize()
        if self.delays:
            self.delays = " ".join(self.delays.split()).capitalize()

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
