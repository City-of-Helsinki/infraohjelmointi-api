import random
import uuid
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as lazy


class ProjectType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField(max_length=200)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstName = models.CharField(max_length=200)
    lastName = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    phone = models.CharField(max_length=14)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)


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
    hkrId = models.UUIDField(blank=True, null=True)
    description = models.TextField(max_length=500, blank=True, null=True)
    # sapProjectNumberList to be acquired using method field
    # sapNetworkNumberList to be acquired using method field
    responsiblePerson = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    phase = models.CharField(
        max_length=16,
        choices=ProjectPhaseChoices.choices,
        default=ProjectPhaseChoices.PROPOSAL,
    )
    programmed = models.BooleanField(default=False)
    # finances = models.TextField(max_length=500, blank=True, null=True)
    def sapProjects(self):
        return [
            sapProject
            for sapProject in list(
                Project.objects.filter(projectSet=self).values_list(
                    "sapProject", flat=True
                )
            )
            if sapProject is not None
        ]

    def sapNetworks(self):
        return [
            sapNetwork
            for sapNetwork in list(
                Project.objects.filter(projectSet=self).values_list(
                    "sapNetwork", flat=True
                )
            )
            if sapNetwork is not None
        ]

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


class ProjectArea(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    areaName = models.CharField(max_length=200, blank=False, null=False)
    location = models.CharField(max_length=200, blank=True, null=True)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)


class BudgetItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budgetMain = models.IntegerField(blank=True, null=True)
    budgetPlan = models.IntegerField(blank=True, null=True)
    site = models.CharField(max_length=200, blank=True, null=True)
    siteName = models.CharField(max_length=200, blank=True, null=True)
    district = models.CharField(max_length=200, blank=True, null=True)
    need = models.DecimalField(max_digits=20, decimal_places=2)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
    # one field left from budget item


class Project(models.Model):
    # PROJECT URL AS A FIELD TO SHARE
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

    class ProjectTypeChoices(models.TextChoices):
        ProjectComplex = "projectComplex", lazy("ProjectComplex")
        Street = "stret", lazy("Street")
        Traffic = "traffic", lazy("Traffic")
        Sports = "sports", lazy("Sports")
        Omastadi = "omastadi", lazy("Omastadi")
        ProjectArea = "projectArea", lazy("ProjectArea")
        Park = "park", lazy("Park")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    siteId = models.ForeignKey(
        BudgetItem, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    hkrId = models.UUIDField(blank=True, null=True)
    sapProject = models.UUIDField(blank=True, null=True)
    sapNetwork = models.UUIDField(blank=True, null=True)
    projectSet = models.ForeignKey(
        ProjectSet, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    area = models.ForeignKey(
        ProjectArea, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    type = models.CharField(max_length=15, choices=ProjectTypeChoices.choices)
    name = models.CharField(max_length=200, blank=False)
    description = models.TextField(max_length=500, blank=True, null=True)
    personPlanning = models.ForeignKey(
        Person, related_name="planning", on_delete=models.DO_NOTHING, null=True
    )
    personProgramming = models.ForeignKey(
        Person, related_name="programming", on_delete=models.DO_NOTHING, null=True
    )
    personConstruction = models.ForeignKey(
        Person, related_name="construction", on_delete=models.DO_NOTHING, null=True
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
        # returns percentage of readiness
        return random.randint(0, 100)

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


class Task(models.Model):
    class TaskStatusChoices(models.TextChoices):
        ACTIVE = "acive", ("Active")
        PAST = "past", ("Past")
        UPCOMING = "upcoming", ("Upcoming")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projectId = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    hkrId = models.UUIDField(blank=True, null=True)
    taskType = models.CharField(max_length=50, blank=False, null=False)
    status = models.CharField(
        max_length=8,
        choices=TaskStatusChoices.choices,
        default=TaskStatusChoices.UPCOMING,
    )
    startDate = models.DateField(auto_now=True, blank=True)
    endDate = models.DateField(auto_now=True, blank=True)
    person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    realizedCost = models.DecimalField(max_digits=20, decimal_places=2)
    plannedCost = models.DecimalField(max_digits=20, decimal_places=2)
    # TaskAccomplishment
    riskAssess = models.CharField(max_length=200, blank=False, null=False)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True)
    updatedDate = models.DateTimeField(auto_now=True, blank=True)
