from django.test import TestCase
from ..models import Project
from ..models import ProjectArea
from ..models import ProjectSet
import uuid
from ..models import BudgetItem
from ..models import Person
from ..models import ProjectType
from ..models import ProjectPhase
from ..models import ProjectPriority
from ..serializers import ProjectGetSerializer
from rest_framework.renderers import JSONRenderer


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
            hkrId=324,
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
        self.projectPhase = ProjectPhase.objects.create(
            id=uuid.uuid4(), value="Proposal"
        )
        self.projectPriority = ProjectPriority.objects.create(
            id=uuid.uuid4(), value="High"
        )

        self.project = Project.objects.create(
            id=self.projectId,
            siteId=self.budgetItem,
            hkrId=12345,
            sapProject=uuid.uuid4(),
            sapNetwork=uuid.uuid4(),
            projectSet=self.projectSet,
            entityName="Sample Entity Name",
            area=self.projectArea,
            type=self.projectType,
            name="Test project 1",
            description="description of the test project",
            personPlanning=self.person_2,
            personProgramming=self.person_1,
            personConstruction=self.person_3,
            phase=self.projectPhase,
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
            priority=self.projectPriority,
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

        self.assertDictEqual(
            self.budgetItem.project_set.all().values()[0],
            Project.objects.filter(id=self.projectId).values()[0],
            msg="siteId foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertDictEqual(
            self.projectSet.project_set.all().values()[0],
            Project.objects.filter(id=self.projectId).values()[0],
            msg="projectSet foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertDictEqual(
            self.projectArea.project_set.all().values()[0],
            Project.objects.filter(id=self.projectId).values()[0],
            msg="projectArea foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertDictEqual(
            self.projectType.project_set.all().values()[0],
            Project.objects.filter(id=self.projectId).values()[0],
            msg="projectType foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertDictEqual(
            self.projectPhase.project_set.all().values()[0],
            Project.objects.filter(id=self.projectId).values()[0],
            msg="projectPhase foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertDictEqual(
            self.projectPriority.project_set.all().values()[0],
            Project.objects.filter(id=self.projectId).values()[0],
            msg="projectPriority foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertDictEqual(
            self.person_3.construction.all().values()[0],
            Project.objects.filter(id=self.projectId).values()[0],
            msg="personConstruction foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertDictEqual(
            self.person_2.planning.all().values()[0],
            Project.objects.filter(id=self.projectId).values()[0],
            msg="personPlanning foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )
        self.assertDictEqual(
            self.person_1.programming.all().values()[0],
            Project.objects.filter(id=self.projectId).values()[0],
            msg="personProgramming foreign key does not exist in Project with id {}".format(
                self.projectId
            ),
        )

    def test_project_manyTomany_relationship_exists(self):
        person_1_reverse_query = self.person_1.favourite.all().values()[0]
        person_2_reverse_query = self.person_2.favourite.all().values()[0]
        self.assertDictEqual(
            person_1_reverse_query,
            person_2_reverse_query,
            msg="Reverse relationship from foriegn key objects do not point to the same Project",
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
            hkrId=2265,
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
            phase=self.projectPhase,
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
            priority=self.projectPriority,
            locked=True,
            comments="Comments random",
            delays="yes 1 delay because of tests",
            hashTags=[],
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
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            len(response.json()), 2, msg="Number of retrieved projects is != 2"
        )

    def test_GET_one_project(self):
        response = self.client.get(
            "/projects/{}/".format(self.projectId),
        )
        # serialize the model instances
        serializer = ProjectGetSerializer(
            Project.objects.get(id=self.projectId), many=False
        )

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected

        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(response.content, result_expected)

    def test_POST_project(self):
        data = {
            "hkrId": None,
            "sapProject": "55dc9624-2cb1-4c11-b15a-c8c97466d127",
            "sapNetwork": "55dc9624-2cb1-4c11-b15a-c8c97466d127",
            "name": "TEST_PROECT_POST",
            "description": "TEST_PROJECT_POST_DESCRIPTION",
            "phase": None,
            "programmed": True,
            "entityName": "Entity for POST",
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
            "priority": None,
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
            "hashTags": ["hash1", "hash2"],
            "budgetForecast1CurrentYear": None,
            "budgetForecast2CurrentYear": None,
            "budgetForecast3CurrentYear": None,
            "budgetForecast4CurrentYear": None,
            "budgetProposalCurrentYearPlus1": None,
            "budgetProposalCurrentYearPlus2": None,
            "preliminaryCurrentYearPlus3": None,
            "preliminaryCurrentYearPlus4": None,
            "preliminaryCurrentYearPlus5": None,
            "preliminaryCurrentYearPlus6": None,
            "preliminaryCurrentYearPlus7": None,
            "preliminaryCurrentYearPlus8": None,
            "preliminaryCurrentYearPlus9": None,
            "preliminaryCurrentYearPlus10": None,
        }
        response = self.client.post(
            "/projects/",
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, msg="Status code != 201")
        # deleting id, projectReadiness because request body doesn't contain an id and project_readiness but the response does if new resource is created
        res_data = response.json()
        new_createdId = res_data["id"]
        del res_data["id"]
        del res_data["projectReadiness"]
        self.assertEqual(res_data, data, msg="Created object != POST data")
        self.assertEqual(
            Project.objects.filter(id=new_createdId).exists(),
            True,
            msg="Project created using POST request does not exist in DB",
        )

    def test_PATCH_project(self):
        data = {
            "name": "Test Project 1 patched",
            "favPersons": [self.person_1.id.__str__(), self.person_3.id.__str__()],
        }
        response = self.client.patch(
            "/projects/{}/".format(self.projectId),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["name"], data["name"], msg="Data not updated in the DB"
        )
        self.assertEqual(
            response.json()["favPersons"],
            data["favPersons"],
            msg="Data not updated in the DB",
        )

    def test_DELETE_project(self):
        response = self.client.delete("/projects/{}/".format(self.projectId))
        self.assertEqual(
            response.status_code,
            204,
            msg="Error deleting project with Id {}".format(self.projectId),
        )
        self.assertEqual(
            Project.objects.filter(id=self.projectId).exists(),
            False,
            msg="Project with Id {} still exists in DB".format(self.projectId),
        )
