from ...models import *
import uuid

projectId = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")
projectId2 = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
budgetItemId = uuid.UUID("5b1b127f-b4c4-4bea-b994-b2c5c04332f8")
person_1_Id = uuid.UUID("2c6dece3-cf93-45ba-867d-8f1dd14923fc")
person_2_Id = uuid.UUID("7fe92cae-d866-4e12-b182-547c367efe12")
person_3_Id = uuid.UUID("b56ae8c8-f5c2-4abe-a1a6-f3a83265ff49")
projectSetId = uuid.UUID("fb093e0e-0b35-4b0e-94d7-97c91997f2d0")
projectAreaId = uuid.UUID("9acb1ac2-259e-4300-8cf0-f89c3adaf577")
projectPhaseId = uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256")
projectTypeId = uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166")
projectPriorityId = uuid.UUID("e7f471fb-6eac-4688-aa9b-908b0194a5dc")
sapNetworkIds_1 = [uuid.UUID("1495aaf7-b0af-4847-a73b-7650145a73dc").__str__()]
sapProjectIds_1 = [uuid.UUID("e6f0805c-0b20-4248-bfae-21cf6bfe744a").__str__()]
sapNetworkIds_2 = [uuid.UUID("1c97fff1-e386-4e43-adc5-131af3cd9e37").__str__()]
sapProjectIds_2 = [uuid.UUID("2cee5e12-eda9-499c-8a3f-f17b2b0b1a98").__str__()]


def mkBudgetItem(
    id=budgetItemId,
    budgetMain=10000,
    budgetPlan=10000,
    site="Helsinki",
    siteName="Anankatu",
    disctrict="Random",
    need=5000,
):
    return BudgetItem.objects.create(
        id=id,
        budgetMain=budgetMain,
        budgetPlan=budgetPlan,
        site=site,
        siteName=siteName,
        district=disctrict,
        need=need,
    )


def mkPerson(
    id=person_1_Id,
    firstName="John",
    lastName="Doe",
    email="random@random.com",
    title="Manager",
    phone="0414853277",
):
    return Person.objects.create(
        id=id,
        firstName=firstName,
        lastName=lastName,
        email=email,
        title=title,
        phone=phone,
    )


def mkProjectPhase(id=projectPhaseId, value="Proposal"):
    return ProjectPhase.objects.create(id=id, value=value)


def mkProjectSet(
    minimal=False,
    id=projectSetId,
    name="Test Project Set",
    hkrId=1234,
    description="This is test project set",
    responsiblePerson=mkPerson(),
    phase=mkProjectPhase(),
    programmed=False,
):
    if minimal == False:
        return (
            ProjectSet.objects.create(
                id=id,
                name=name,
                hkrId=hkrId,
                description=description,
                responsiblePerson=responsiblePerson,
                phase=phase,
                programmed=programmed,
            ),
            responsiblePerson,
            phase,
        )
    else:
        return ProjectSet.objects.create(
            id=id,
            name=name,
            hkrId=hkrId,
            description=description,
            responsiblePerson=responsiblePerson,
            phase=phase,
            programmed=programmed,
        )


def mkProjectArea(id=projectAreaId, value="honkasuo", location="Helsinki"):
    return ProjectArea.objects.create(
        id=id,
        value=value,
        location=location,
    )


def mkProject(minimal=False):
    if minimal == False:
        budgetItem = mkBudgetItem(id=budgetItemId)
        person_1 = mkPerson(id=person_1_Id)
        person_2 = mkPerson(
            id=person_2_Id, firstName="John", lastName="Doe 2", title="CEO"
        )
        person_3 = mkPerson(
            id=person_3_Id,
            firstName="John",
            lastName="Doe 3",
            title="Contractor",
        )
        projectPhase = mkProjectPhase(id=projectPhaseId)
        projectSet = mkProjectSet(
            minimal=True,
            id=projectSetId,
            responsiblePerson=person_1,
            phase=projectPhase,
        )
        projectArea = mkProjectArea(id=projectAreaId)
    ## left it off here
    projectType = ProjectType.objects.create(id=projectTypeId, value="projectComplex")

    projectPriority = ProjectPriority.objects.create(id=projectPriorityId, value="High")

    project = Project.objects.create(
        id=projectId,
        siteId=budgetItem,
        hkrId=12345,
        sapProject=sapProjectIds_1,
        sapNetwork=sapNetworkIds_1,
        projectSet=projectSet,
        entityName="Sample Entity Name",
        area=projectArea,
        type=projectType,
        name="Test project 1",
        description="description of the test project",
        personPlanning=person_2,
        personProgramming=person_1,
        personConstruction=person_3,
        phase=projectPhase,
        programmed=True,
        constructionPhaseDetail="Current phase is proposal",
        estPlanningStartYear=2022,
        estDesignEndYear=2023,
        estDesignStartDate="2022-11-20",
        estDesignEndDate="2022-11-28",
        contractPrepStartDate="2022-11-20",
        contractPrepEndDate="2022-11-20",
        warrantyStartDate="2022-11-20",
        warrantyExpireDate="2022-11-20",
        perfAmount=20000.00,
        unitCost=10000.00,
        costForecast=10000.00,
        neighborhood="my random neigbhorhood",
        comittedCost=120.0,
        tiedCurrYear=12000.00,
        realizedCost=20.00,
        spentCost=20000.00,
        riskAssess="Yes very risky test",
        priority=projectPriority,
        locked=True,
        comments="Comments random",
        delays="yes 1 delay because of tests",
        hashTags=["#random", "#random2"],
        budgetForecast1CurrentYear=None,
        budgetForecast2CurrentYear=None,
        budgetForecast3CurrentYear=None,
        budgetForecast4CurrentYear=None,
        budgetProposalCurrentYearPlus1=None,
        budgetProposalCurrentYearPlus2=None,
        preliminaryCurrentYearPlus3=None,
        preliminaryCurrentYearPlus4=None,
        preliminaryCurrentYearPlus5=None,
        preliminaryCurrentYearPlus6=None,
        preliminaryCurrentYearPlus7=None,
        preliminaryCurrentYearPlus8=None,
        preliminaryCurrentYearPlus9=None,
        preliminaryCurrentYearPlus10=None,
    )
    project.favPersons.add(person_1, person_2)
