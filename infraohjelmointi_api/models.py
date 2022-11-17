import uuid
from django.db import models
from django.utils.timezone import now


class ProjectType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField(max_length=200)


class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    phone = models.IntegerField(max_length=12)


class ProjectSet(models.Model):
    class ProjectPhaseChoices(models.TextChoices):
        PROPOSAL = "PROP", ("Hanke-ehdotus")
        DESIGN = "DESG", ("Yleissuunnittelu")
        PROGRAMMING = "PROG", ("Ohjelmointi")
        DRAFT_INITIATION = "DRAI", (
            "Katu- ja puistosuunnittelun aloitus/suunnitelmaluonnos"
        )
        DRAFT_APPROVAL = "DRAA", ("Katu-/puistosuunnitelmaehdotus ja hyväksyminen")
        CONSTRUCTION_PLAN = "CONP", ("Rakennussuunnitelma")
        CONSTRUCTION_WAIT = "CONW", ("Odottaa rakentamista")
        CONSTRUCTION = "CONS", ("Rakentaminen")
        WARRANTY_PERIOD = "WARP", ("Takuuaika")
        COMPLETED = "COMP", ("Valmis / ylläpidossa")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, blank=True, null=True)
    pwProjectId = models.UUIDField(blank=True, null=True)
    description = models.TextField(max_length=500, blank=True, null=True)
    # sapProjectNumberList to be acquired using method field
    # sapNetworkNumberList to be acquired using method field
    responsiblePerson = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    projectPhase = models.CharField(
        max_length=4,
        choices=ProjectPhaseChoices.choices,
        default=ProjectPhaseChoices.PROPOSAL,
    )
    programmed = models.BooleanField(default=False)
    # finances = models.TextField(max_length=500, blank=True, null=True)


class ProjectArea(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    areaName = models.CharField(max_length=200, blank=False, null=False)
    location = models.CharField(max_length=200, blank=True, null=True)


class BudgetItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budgetMain = models.IntegerField(blank=True, null=True)
    budgetPlan = models.IntegerField(blank=True, null=True)
    site = models.CharField(max_length=200, blank=True, null=True)
    siteName = models.CharField(max_length=200, blank=True, null=True)
    district = models.CharField(max_length=200, blank=True, null=True)
    need = models.DecimalField(max_digits=6, decimal_places=2)
    # one field left from budget item


class Project(models.Model):
    # PROJECT URL AS A FIELD TO SHARE
    class ProjectPhaseChoices(models.TextChoices):
        PROPOSAL = "PROP", ("Hanke-ehdotus")
        DESIGN = "DESG", ("Yleissuunnittelu")
        PROGRAMMING = "PROG", ("Ohjelmointi")
        DRAFT_INITIATION = "DRAI", (
            "Katu- ja puistosuunnittelun aloitus/suunnitelmaluonnos"
        )
        DRAFT_APPROVAL = "DRAA", ("Katu-/puistosuunnitelmaehdotus ja hyväksyminen")
        CONSTRUCTION_PLAN = "CONP", ("Rakennussuunnitelma")
        CONSTRUCTION_WAIT = "CONW", ("Odottaa rakentamista")
        CONSTRUCTION = "CONS", ("Rakentaminen")
        WARRANTY_PERIOD = "WARP", ("Takuuaika")
        COMPLETED = "COMP", ("Valmis / ylläpidossa")

    class PriorityChoices(models.TextChoices):
        LOW = "L", ("Low")
        MEDIUM = "M", ("Medium")
        HIGH = "H", ("High")

    class ProjectTypeChoices(models.TextChoices):
        ProjectComplex = "PROJECTCOMPLEX", ("Hankekokonaisuus")
        Street = "STREET", ("Katu")
        Traffic = "TRAFFIC", ("Liikenne")
        Sports = "SPORTS", ("Liikunta")
        Omastadi = "OMASTADI", ("Omastadi")
        ProjectArea = "PROJECTAREA", ("Projektialue")
        Park = "PARK", ("Puisto tai taitorakenne")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    siteId = models.ForeignKey(
        BudgetItem, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    pwProjectId = models.UUIDField(blank=True, null=True)
    sapProjectNumber = models.UUIDField(blank=True, null=True)
    sapNetworkNumber = models.UUIDField(blank=True, null=True)
    projectSet = models.ForeignKey(
        ProjectSet, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    projectArea = models.ForeignKey(
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
    projectPhase = models.CharField(
        max_length=4,
        choices=ProjectPhaseChoices.choices,
        default=ProjectPhaseChoices.PROPOSAL,
    )
    favPersons = models.ManyToManyField(Person, related_name="favourite")
    programmed = models.BooleanField(default=False)
    constructionPhaseDetail = models.TextField(max_length=500, blank=True, null=True)
    estPlanningStartYear = models.IntegerField(blank=True, null=True)
    estDesignEndYear = models.IntegerField(blank=True, null=True)
    estDesignStartDate = models.DateTimeField(blank=True, null=True)
    estDesignEndDate = models.DateTimeField(blank=True, null=True)
    contractPrepStartDate = models.DateTimeField(blank=True, null=True)
    contractPrepEndDate = models.DateTimeField(blank=True, null=True)
    warrantyStartDate = models.DateTimeField(blank=True, null=True)
    warrantyExpireDate = models.DateTimeField(blank=True, null=True)
    perfAmount = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    unitCost = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    costForecast = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    neighborhood = models.CharField(max_length=200, blank=True, null=True)
    comittedCost = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    tiedCurrYear = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    realizedCost = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    spentCost = models.DecimalField(
        max_digits=6, decimal_places=2, blank=True, null=True
    )
    riskAssess = models.CharField(max_length=200, blank=True, null=True)
    priority = models.CharField(
        max_length=2,
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

    created_date = models.DateTimeField(auto_now_add=True, blank=True)
    updated_date = models.DateTimeField(auto_now=True, blank=True)

    # Rediness % to be calculated

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["id", "pwProjectId", "sapProjectNumber", "sapNetworkNumber"],
                name="Unique together Project Ids",
            )
        ]


class Task(models.Model):
    class TaskStatusChoices(models.TextChoices):
        ACTIVE = "A", ("Active")
        PAST = "P", ("Past")
        UPCOMING = "U", ("Upcoming")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    projectId = models.ForeignKey(Project, on_delete=models.DO_NOTHING)
    pwProjectId = models.UUIDField(blank=True, null=True)
    taskType = models.CharField(max_length=50, blank=False, null=False)
    status = models.CharField(
        max_length=2,
        choices=TaskStatusChoices.choices,
        default=TaskStatusChoices.UPCOMING,
    )
    startDate = models.DateTimeField(auto_now=True, blank=True)
    endDate = models.DateTimeField(auto_now=True, blank=True)
    person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    realizedCost = models.DecimalField(max_digits=6, decimal_places=2)
    plannedCost = models.DecimalField(max_digits=6, decimal_places=2)
    # TaskAccomplishment
    riskAssess = models.CharField(max_length=200, blank=False, null=False)
