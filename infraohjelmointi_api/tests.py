from django.test import TestCase

from infraohjelmointi_api.serializers import (
    ProjectCreateSerializer,
    ProjectGetSerializer,
)
from .models import Project
from .models import ProjectArea
from .models import ProjectSet
import uuid
from .models import BudgetItem
from .models import Person
from .models import ProjectType
import io
from rest_framework.parsers import JSONParser


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
        self.assertTrue(
            Project.objects.filter(id=self.projectId).exists(),
            msg="Object does not exist in DB",
        )
        project = Project.objects.get(id=self.projectId)
        self.assertIsInstance(
            project, Project, msg="Object retrieved from DB != typeof Project Model"
        )
        self.assertEqual(project, self.project, msg="Object from DB != created Object")

    def test_project_foreign_keys_exists(self):
        project = Project.objects.get(id=self.projectId)
        self.assertEqual(
            project.siteId.id,
            self.budgetItem.id,
            msg="siteId foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertEqual(
            project.projectSet.id,
            self.projectSet.id,
            msg="BudgetItem foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertEqual(
            project.area.id,
            self.projectArea.id,
            msg="ProjectArea foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertEqual(
            project.type.id,
            self.projectType.id,
            msg="ProjectType foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertEqual(
            project.personConstruction.id,
            self.person_3.id,
            msg="personConstruction foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertEqual(
            project.personPlanning.id,
            self.person_2.id,
            msg="personPlanning foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertEqual(
            project.personProgramming.id,
            self.person_1.id,
            msg="personProgramming foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )

    def test_project_manyTomany_relationship_exists(self):
        project = Project.objects.get(id=self.projectId)
        self.assertEqual(
            project.favPersons.get(id=self.person_1.id),
            self.person_1,
            msg="Person with id {} does not exist in the field".format(
                self.person_1.id
            ),
        )
        self.assertEqual(
            project.favPersons.get(id=self.person_2.id),
            self.person_2,
            msg="Person with id {} does not exist in the field".format(
                self.person_2.id
            ),
        )

    def test_GET_all_projects(self):
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            len(response.json()), 1, msg="Number of retrieved projects is != 1"
        )
        Project.objects.create(
            id=uuid.uuid4(),
            siteId=self.budgetItem,
            hkrId=uuid.uuid4(),
            sapProject=uuid.uuid4(),
            sapNetwork=uuid.uuid4(),
            projectSet=self.projectSet,
            area=self.projectArea,
            type=self.projectType,
            name="Test project 2",
            description="description of the test project 2",
            personPlanning=self.person_2,
            personProgramming=self.person_1,
            personConstruction=self.person_3,
            phase="proposal",
            programmed=True,
            constructionPhaseDetail="Current phase is proposal 2",
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
            neighborhood="my random neigbhorhood 2",
            comittedCost=120.0,
            tiedCurrYear=12000.00,
            realizedCost=20.00,
            spentCost=20000.00,
            riskAssess="Yes very risky test 2",
            priority="low",
            locked=True,
            comments="Comments random",
            delays="yes 1 delay because of tests",
        )
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            len(response.json()), 2, msg="Number of retrieved projects is != 2"
        )

    def test_GET_one_project(self):
        response = self.client.get(
            "/projects/{}/".format(self.projectId),
        )
        self.assertEqual(response.status_code, 200, msg="Status code != 200")

    def test_POST_project(self):
        data = {
            "hkrId": None,
            "sapProject": "55dc9624-2cb1-4c11-b15a-c8c97466d127",
            "sapNetwork": "55dc9624-2cb1-4c11-b15a-c8c97466d127",
            "name": "TEST_PROECT_POST",
            "description": "TEST_PROJECT_POST_DESCRIPTION",
            "phase": "proposal",
            "programmed": True,
            "constructionPhaseDetail": None,
            "estPlanningStartYear": None,
            "estDesignEndYear": None,
            "estDesignStartDate": None,
            "estDesignEndDate": None,
            "contractPrepStartDate": None,
            "contractPrepEndDate": None,
            "warrantyStartDate": None,
            "warrantyExpireDate": None,
            "perfAmount": None,
            "unitCost": None,
            "costForecast": None,
            "neighborhood": None,
            "comittedCost": None,
            "tiedCurrYear": None,
            "realizedCost": None,
            "spentCost": None,
            "riskAssess": None,
            "priority": "medium",
            "locked": False,
            "comments": None,
            "delays": None,
            "siteId": None,
            "projectSet": None,
            "area": None,
            "type": None,
            "personPlanning": None,
            "personProgramming": None,
            "personConstruction": None,
            "favPersons": [self.person_1.id.__str__()],
        }
        response = self.client.post(
            "/projects/",
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, msg="Status code != 201")
        # deleting id, projectReadiness, createdDate and updatedDate because request body doesn't contain an id and project_readiness but the response does if new resource is created
        res_data = response.json()
        del res_data["id"]
        del res_data["projectReadiness"]
        del res_data["createdDate"]
        del res_data["updatedDate"]
        self.assertEqual(res_data, data, msg="Created object != POST data")
