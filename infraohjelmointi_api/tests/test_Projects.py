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
from ..models import Note
from ..serializers import ProjectGetSerializer
from ..serializers import NoteSerializer

from rest_framework.renderers import JSONRenderer
from overrides import override


class ProjectTestCase(TestCase):
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
    sapProjectId = "2814I00708"
    sapNetworkIds_2 = [uuid.UUID("1c97fff1-e386-4e43-adc5-131af3cd9e37").__str__()]
    sapProjectId_2 = "2814I00718"
    noteId = uuid.UUID("2e91feba-13c1-4b4a-a3a1-ca2030bf8681")
    fixtures = []

    @classmethod
    @override
    def setUpTestData(self):
        self.budgetItem = BudgetItem.objects.create(
            id=self.budgetItemId,
            budgetMain=10000,
            budgetPlan=10000,
            site="Helsinki",
            siteName="Anankatu",
            district="doe",
            need=5000.0,
        )
        self.person_1 = Person.objects.create(
            id=self.person_1_Id,
            firstName="John",
            lastName="Doe",
            email="random@random.com",
            title="Manager",
            phone="0414853275",
        )
        self.person_2 = Person.objects.create(
            id=self.person_2_Id,
            firstName="John",
            lastName="Doe 2",
            email="random@random.com",
            title="CEO",
            phone="0414853275",
        )
        self.person_3 = Person.objects.create(
            id=self.person_3_Id,
            firstName="John",
            lastName="Doe 3",
            email="random@random.com",
            title="Contractor",
            phone="0414853275",
        )
        self.projectPhase = ProjectPhase.objects.create(
            id=self.projectPhaseId, value="Proposal"
        )
        self.projectSet = ProjectSet.objects.create(
            id=self.projectSetId,
            name="Project Set 1",
            hkrId=324,
            description="This is test project Set 1",
            responsiblePerson=self.person_2,
            phase=self.projectPhase,
            programmed=True,
        )
        self.projectArea = ProjectArea.objects.create(
            id=self.projectAreaId,
            value="Hervanta",
            location="inisnoorinkatu 60c",
        )
        self.projectType = ProjectType.objects.create(
            id=self.projectTypeId, value="projectComplex"
        )

        self.projectPriority = ProjectPriority.objects.create(
            id=self.projectPriorityId, value="High"
        )

        self.project = Project.objects.create(
            id=self.projectId,
            siteId=self.budgetItem,
            hkrId=12345,
            sapProject=self.sapProjectId,
            sapNetwork=self.sapNetworkIds_1,
            projectSet=self.projectSet,
            entityName="Sample Entity Name",
            area=self.projectArea,
            type=self.projectType,
            name="Test project 1",
            address="Insinoorinkatu 60 D",
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
            msg="Reverse relationship from manyTomany key objects do not point to the same Project",
        )

    def test_GET_all_projects(self):
        response = self.client.get("/projects/")
        projectCount = Project.objects.all().count()
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            len(response.json()),
            projectCount,
            msg="Number of retrieved projects is != {}".format(projectCount),
        )
        Project.objects.create(
            id=self.projectId2,
            siteId=self.budgetItem,
            hkrId=2265,
            sapProject=self.sapProjectId_2,
            sapNetwork=self.sapNetworkIds_2,
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
            len(response.json()),
            projectCount + 1,
            msg="Number of retrieved projects is != {}".format(projectCount + 1),
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
        self.assertEqual(
            response.content,
            result_expected,
            msg="Project data in response != Project data in DB",
        )

    def test_POST_project(self):
        data = {
            "category": None,
            "effectHousing": False,
            "hkrId": None,
            "sapProject": "2814I00708",
            "sapNetwork": ["55dc9624-2cb1-4c11-b15a-c8c97466d127"],
            "name": "TEST_PROECT_POST",
            "address": "Herttoniemi street 123 3b",
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
        # deleting id and projectReadiness because request body doesn't contain an id and
        #  but the response does if new resource is created
        res_data = response.json()
        new_createdId = res_data["id"]
        del res_data["id"]
        del res_data["projectReadiness"]
        self.assertEqual(res_data, data, msg="Created object data != POST data")
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
            response.json()["name"],
            data["name"],
            msg="Data: name sent through PATCH != Data: name in the DB",
        )
        self.assertEqual(
            response.json()["favPersons"],
            data["favPersons"],
            msg="Data: favPersons sent through PATCH != Data: favPersons in the DB",
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

    def test_notes_project(self):
        Note.objects.create(
            id=self.noteId,
            content="Test note",
            updatedBy=self.person_1,
            project=self.project,
        )
        response = self.client.get("/projects/{}/notes/".format(self.projectId))
        serializer = NoteSerializer(Note.objects.filter(id=self.noteId), many=True)

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            response.content,
            result_expected,
            msg="Note data in response != Note data in DB",
        )

    def test_string_sanitization_project(self):
        data = {
            "name": "   test      project.  name   ",
            "address": "  Address.    works   for me.",
            "description": " random Description   works.  yes    ",
            "entityName": "Entity Name",
            "delays": "    100 delays   .",
            "riskAssess": " risky   risky  .   Matter   this ",
            "comments": "This comment is    random    ",
        }

        validData = {
            "name": "test project. name",
            "address": "Address. works for me.",
            "description": "random Description works. yes",
            "entityName": "Entity Name",
            "delays": "100 delays .",
            "riskAssess": "risky risky . Matter this",
            "comments": "This comment is random",
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
        self.assertEqual(
            res_data["name"],
            validData["name"],
            msg="Field: name not trimmed successfully",
        )
        self.assertEqual(
            res_data["address"],
            validData["address"],
            msg="Field: address not trimmed successfully",
        )
        self.assertEqual(
            res_data["description"],
            validData["description"],
            msg="Field: description not trimmed successfully",
        )
        self.assertEqual(
            res_data["entityName"],
            validData["entityName"],
            msg="Field: entityName not trimmed successfully",
        )
        self.assertEqual(
            res_data["delays"],
            validData["delays"],
            msg="Field: delays not trimmed successfully",
        )
        self.assertEqual(
            res_data["riskAssess"],
            validData["riskAssess"],
            msg="Field: riskAssess not trimmed successfully",
        )
        self.assertEqual(
            res_data["comments"],
            validData["comments"],
            msg="Field: comments not trimmed successfully",
        )
        self.assertEqual(
            Project.objects.filter(id=new_createdId).exists(),
            True,
            msg="Project created using POST request does not exist in DB",
        )
