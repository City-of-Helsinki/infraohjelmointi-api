from django.test import TestCase
from .models import Project
from .models import ProjectArea
from .models import ProjectSet
import uuid
from .models import BudgetItem
from .models import Person
from .models import ProjectType


class ProjectTestCase(TestCase):
    projectId = uuid.uuid4()
    fixtures = []

    @classmethod
    def setUpTestData(self):
        self.budgetItem = BudgetItem.objects.create(
            id=uuid.uuid4(),
            budgetMain=10000,
            budgetPlan=10000,
            site="Helsinki",
            siteName="Anankatu",
            district="doe",
            need=5000.0,
        )
        self.person_1 = Person.objects.create(
            id=uuid.uuid4(),
            firstName="John",
            lastName="Doe",
            email="random@random.com",
            title="Manager",
            phone="0414853275",
        )
        self.person_2 = Person.objects.create(
            id=uuid.uuid4(),
            firstName="John",
            lastName="Doe 2",
            email="random@random.com",
            title="CEO",
            phone="0414853275",
        )
        self.person_3 = Person.objects.create(
            id=uuid.uuid4(),
            firstName="John",
            lastName="Doe 3",
            email="random@random.com",
            title="Contractor",
            phone="0414853275",
        )

        self.projectSet = ProjectSet.objects.create(
            id=uuid.uuid4(),
            name="Project Set 1",
            hkrId=uuid.uuid4(),
            description="This is test project Set 1",
            responsiblePerson=self.person_2,
            phase="proposal",
            programmed=True,
        )
        self.projectArea = ProjectArea.objects.create(
            id=uuid.uuid4(),
            areaName="Hervanta",
            location="inisnoorinkatu 60c",
        )
        self.projectType = ProjectType.objects.create(
            id=uuid.uuid4(), value="projectComplex"
        )

        self.project = Project.objects.create(
            id=self.projectId,
            siteId=self.budgetItem,
            hkrId=uuid.uuid4(),
            sapProject=uuid.uuid4(),
            sapNetwork=uuid.uuid4(),
            projectSet=self.projectSet,
            area=self.projectArea,
            type=self.projectType,
            name="Test project 1",
            description="description of the test project",
            personPlanning=self.person_2,
            personProgramming=self.person_1,
            personConstruction=self.person_3,
            phase="proposal",
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
            priority="low",
            locked=True,
            comments="Comments random",
            delays="yes 1 delay because of tests",
        )
        self.project.favPersons.add(self.person_1, self.person_2)

    def test_project_is_created(self):
        project = Project.objects.get(id=self.projectId)
        self.assertTrue(project)
        self.assertIsInstance(project, Project)
        self.assertEquals(project, self.project)
