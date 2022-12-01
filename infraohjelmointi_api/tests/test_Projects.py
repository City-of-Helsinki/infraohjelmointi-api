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
from overrides import override
from infraohjelmointi_api.utils import DataGen


class ProjectTestCase(TestCase):
    projectId = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")
    projectId2 = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    budgetItemId = uuid.UUID("5b1b127f-b4c4-4bea-b994-b2c5c04332f8")
    projectSetId = uuid.UUID("fb093e0e-0b35-4b0e-94d7-97c91997f2d0")
    person_1_Id = uuid.UUID("2c6dece3-cf93-45ba-867d-8f1dd14923fc")
    person_2_Id = uuid.UUID("7fe92cae-d866-4e12-b182-547c367efe12")
    person_3_Id = uuid.UUID("b56ae8c8-f5c2-4abe-a1a6-f3a83265ff49")
    person_4_Id = uuid.UUID("f627e782-81de-4c37-b1f7-ef4c26eeeb99")
    projectAreaId = uuid.UUID("9acb1ac2-259e-4300-8cf0-f89c3adaf577")
    projectTypeId = uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166")
    projectPhaseId = uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256")
    projectPriorityId = uuid.UUID("e7f471fb-6eac-4688-aa9b-908b0194a5dc")

    @classmethod
    @override
    def setUpTestData(self):

        self.budgetItem = DataGen.mkBudgetItem(id=self.budgetItemId)
        self.person_1 = DataGen.mkPerson(id=self.person_1_Id)
        self.person_2 = DataGen.mkPerson(id=self.person_2_Id)
        self.person_3 = DataGen.mkPerson(id=self.person_3_Id)
        self.projectSet = DataGen.mkProjectSet(
            id=self.projectSetId, responsiblePerson=self.person_1
        )
        self.projectArea = DataGen.mkProjectArea(id=self.projectAreaId)
        self.projectType = DataGen.mkProjectType(id=self.projectTypeId)
        self.projectPhase = DataGen.mkProjectPhase(id=self.projectPhaseId)
        self.projectPriority = DataGen.mkProjectPriority(id=self.projectPriorityId)
        self.project = DataGen.mkProject(
            id=self.projectId,
            siteId=self.budgetItem,
            personPlanning=self.person_2,
            personProgramming=self.person_1,
            personConstruction=self.person_3,
            projectSet=self.projectSet,
            area=self.projectArea,
            phase=self.projectPhase,
            priority=self.projectPriority,
            prType=self.projectType,
        )
        self.project.favPersons.add(self.person_1.id, self.person_2.id)

    def test_project_is_created(self):
        self.assertTrue(
            Project.objects.filter(id=self.project.id).exists(),
            msg="Object does not exist in DB",
        )
        project = Project.objects.get(id=self.project.id)
        self.assertIsInstance(
            project, Project, msg="Object retrieved from DB != typeof Project Model"
        )
        self.assertEqual(project, self.project, msg="Object from DB != created Object")

    def test_project_foreign_keys_exists(self):

        self.assertDictEqual(
            self.budgetItem.project_set.all().values()[0],
            Project.objects.filter(id=self.project.id).values()[0],
            msg="siteId foreign key does not exist in Project with id {}".format(
                self.project.id
            ),
        )
        self.assertDictEqual(
            self.projectSet.project_set.all().values()[0],
            Project.objects.filter(id=self.project.id).values()[0],
            msg="projectSet foreign key does not exist in Project with id {}".format(
                self.project.id
            ),
        )
        self.assertDictEqual(
            self.projectArea.project_set.all().values()[0],
            Project.objects.filter(id=self.project.id).values()[0],
            msg="projectArea foreign key does not exist in Project with id {}".format(
                self.project.id
            ),
        )
        self.assertDictEqual(
            self.projectType.project_set.all().values()[0],
            Project.objects.filter(id=self.project.id).values()[0],
            msg="projectType foreign key does not exist in Project with id {}".format(
                self.project.id
            ),
        )
        self.assertDictEqual(
            self.projectPhase.project_set.all().values()[0],
            Project.objects.filter(id=self.project.id).values()[0],
            msg="projectPhase foreign key does not exist in Project with id {}".format(
                self.project.id
            ),
        )
        self.assertDictEqual(
            self.projectPriority.project_set.all().values()[0],
            Project.objects.filter(id=self.project.id).values()[0],
            msg="projectPriority foreign key does not exist in Project with id {}".format(
                self.project.id
            ),
        )
        self.assertDictEqual(
            self.person_3.construction.all().values()[0],
            Project.objects.filter(id=self.project.id).values()[0],
            msg="personConstruction foreign key does not exist in Project with id {}".format(
                self.project.id
            ),
        )
        self.assertDictEqual(
            self.person_2.planning.all().values()[0],
            Project.objects.filter(id=self.project.id).values()[0],
            msg="personPlanning foreign key does not exist in Project with id {}".format(
                self.project.id
            ),
        )
        self.assertDictEqual(
            self.person_1.programming.all().values()[0],
            Project.objects.filter(id=self.project.id).values()[0],
            msg="personProgramming foreign key does not exist in Project with id {}".format(
                self.project.id
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
        DataGen.mkProject(id=self.projectId2)
        response = self.client.get("/projects/")
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            len(response.json()), 2, msg="Number of retrieved projects is != 2"
        )

    def test_GET_one_project(self):
        response = self.client.get(
            "/projects/{}/".format(self.project.id),
        )
        # serialize the model instances
        serializer = ProjectGetSerializer(
            Project.objects.get(id=self.project.id), many=False
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
        # deleting id because request body doesn't contain an id and
        #  but the response does if new resource is created
        res_data = response.json()
        new_createdId = res_data["id"]
        del res_data["id"]
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
            "/projects/{}/".format(self.project.id),
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
        response = self.client.delete("/projects/{}/".format(self.project.id))
        self.assertEqual(
            response.status_code,
            204,
            msg="Error deleting project with Id {}".format(self.project.id),
        )
        self.assertEqual(
            Project.objects.filter(id=self.project.id).exists(),
            False,
            msg="Project with Id {} still exists in DB".format(self.project.id),
        )
