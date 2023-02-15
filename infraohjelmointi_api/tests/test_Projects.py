from django.test import TestCase
import uuid
from ..models import (
    Project,
    ProjectArea,
    ProjectSet,
    BudgetItem,
    Person,
    ProjectType,
    ProjectPhase,
    ProjectPriority,
    ProjectCategory,
    ConstructionPhaseDetail,
    Note,
    ProjectQualityLevel,
    PlanningPhase,
    ConstructionPhase,
    ProjectClass,
    ProjectLocation,
    ProjectHashTag,
    ProjectGroup,
    ProjectLock,
)
from ..serializers import ProjectGetSerializer, ProjectNoteGetSerializer

from rest_framework.renderers import JSONRenderer
from overrides import override


class ProjectTestCase(TestCase):
    project_1_Id = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")
    project_2_Id = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    project_3_Id = uuid.UUID("fdc89f56-b631-4109-a137-45b950de6b10")
    project_4_Id = uuid.UUID("7c5b981e-286f-4065-9d9e-29d8d1714e4c")
    project_5_Id = uuid.UUID("441d80e1-9ab1-4b35-91cc-6017ea308d87")
    project_6_Id = uuid.UUID("90852adc-d47e-4fd9-944f-cb8d36076c21")
    budgetItemId = uuid.UUID("5b1b127f-b4c4-4bea-b994-b2c5c04332f8")
    person_1_Id = uuid.UUID("2c6dece3-cf93-45ba-867d-8f1dd14923fc")
    person_2_Id = uuid.UUID("7fe92cae-d866-4e12-b182-547c367efe12")
    person_3_Id = uuid.UUID("b56ae8c8-f5c2-4abe-a1a6-f3a83265ff49")
    projectSetId = uuid.UUID("fb093e0e-0b35-4b0e-94d7-97c91997f2d0")
    projectAreaId = uuid.UUID("9acb1ac2-259e-4300-8cf0-f89c3adaf577")
    projectPhase_1_Id = uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256")
    projectPhase_2_Id = uuid.UUID("562e3d4f-77ac-4b0c-a82a-4b5bff8daa74")
    projectTypeId = uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166")
    projectPriorityId = uuid.UUID("e7f471fb-6eac-4688-aa9b-908b0194a5dc")
    sapNetworkIds_1 = [uuid.UUID("1495aaf7-b0af-4847-a73b-7650145a73dc").__str__()]
    sapProjectId = "2814I00708"
    sapNetworkIds_2 = [uuid.UUID("1c97fff1-e386-4e43-adc5-131af3cd9e37").__str__()]
    sapProjectId_2 = "2814I00718"
    noteId = uuid.UUID("2e91feba-13c1-4b4a-a3a1-ca2030bf8681")
    projectCategory_1_Id = uuid.UUID("dbc92a70-8a8a-4a25-8014-14c7d16eb86c")
    projectCategory_2_Id = uuid.UUID("4124f82a-4d62-4f66-b021-c45c64ba750a")
    projectCategory_3_Id = uuid.UUID("8a19b04a-15f6-448d-95d3-70fdfa2d5cba")
    conPhaseDetailId = uuid.UUID("a7517b59-40f2-4b7d-a146-eef1a3d08c03")
    projectQualityLevelId = uuid.UUID("05eb79f5-18c3-40a4-b5c4-22c68a216dec")
    planningPhaseId = uuid.UUID("78570e7c-58b8-4d08-a341-a6c95ad58fed")
    constructionPhaseId = uuid.UUID("c37576af-accf-46aa-8df2-5724ff8a06af")
    projectClass_1_Id = uuid.UUID("5f65a339-b3c9-48ee-a9b9-cb177546c241")
    projectClass_2_Id = uuid.UUID("c03b41d4-bb50-4bc5-ada1-496f399eb157")
    projectSubClass_1_Id = uuid.UUID("88006f5b-339d-4859-9903-25494deebeca")
    projectSubClass_2_Id = uuid.UUID("48e201a9-7579-42fe-9970-2c0704bd7257")
    projectMasterClass_1_Id = uuid.UUID("78570e7c-58b8-4d08-a341-a6c95ad58fed")
    projectMasterClass_2_Id = uuid.UUID("073e1dee-9e77-4ddd-8d0c-ad856c51e857")
    projectMasterClass_3_Id = uuid.UUID("a66db3fa-eb71-42dc-b618-9e4fae0db8bc")
    projectHashTag_1_Id = uuid.UUID("e4d7b4b0-830d-4310-8b29-3c7d1e3132ba")
    projectHashTag_2_Id = uuid.UUID("eb8635b3-4e83-45d9-a1af-6bc49bf2aeb7")
    projectHashTag_3_Id = uuid.UUID("aba0e241-0a02-48a0-8426-e4f034c5f527")
    projectHashTag_4_Id = uuid.UUID("5057f0e5-bdcd-4278-a433-74db4ee34b4b")
    projectMainDistrict_1_Id = uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256")
    projectMainDistrict_2_Id = uuid.UUID("740d6771-442b-4713-8362-8bda3958100e")
    projectMainDistrict_3_Id = uuid.UUID("019eb15d-cfdb-45bc-b1a5-ac3844381e48")
    projectDistrict_1_Id = uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166")
    projectDistrict_2_Id = uuid.UUID("e8f68255-5111-4ab5-b346-016956c671d1")
    projectSubDistrict_1_Id = uuid.UUID("191f9acf-e387-4307-93db-b9f252ec18ff")
    projectSubDistrict_2_Id = uuid.UUID("99c4a023-b246-4b1c-be49-848b82b12095")
    projectGroup_1_Id = uuid.UUID("bbba45f2-b0d4-4297-b0e2-4e60f8fa8412")
    projectGroup_2_Id = uuid.UUID("bee657d4-a2cc-4c04-a75b-edc12275dd62")
    projectGroup_3_Id = uuid.UUID("b2e2808c-831b-4db2-b0a8-f6c6d270af1a")

    fixtures = []
    maxDiff = None

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
        self.projectHashTag_1 = ProjectHashTag.objects.create(
            id=self.projectHashTag_1_Id, value="Hash1"
        )
        self.projectHashTag_2 = ProjectHashTag.objects.create(
            id=self.projectHashTag_2_Id, value="Hash2"
        )
        self.mainDistrict = ProjectLocation.objects.create(
            id=self.projectMainDistrict_1_Id, name="Test main district", parent=None
        )
        self.projectLocation = self.mainDistrict.childLocation.create(
            id=self.projectDistrict_1_Id, name="Test district"
        )
        self.projectCategory = ProjectCategory.objects.create(
            id=self.projectCategory_1_Id, value="K5"
        )
        self.projectMasterClass = ProjectClass.objects.create(
            id=self.projectMasterClass_1_Id, name="Test Master Class", parent=None
        )
        self.projectClass = self.projectMasterClass.childClass.create(
            name="Test Class", id=self.projectClass_1_Id
        )
        self.constructionPhase = ConstructionPhase.objects.create(
            id=self.constructionPhaseId, value="planning"
        )
        self.planningPhase = PlanningPhase.objects.create(
            id=self.planningPhaseId, value="projectPlanning"
        )
        self.projectQualityLevel = ProjectQualityLevel.objects.create(
            id=self.projectQualityLevelId, value="A1"
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
        self.conPhaseDetail = ConstructionPhaseDetail.objects.create(
            id=self.conPhaseDetailId, value="preConstruction"
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
            id=self.projectPhase_1_Id, value="Proposal"
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
            otherPersons="Other Test Person",
            projectClass=self.projectClass,
            id=self.project_1_Id,
            projectLocation=self.projectLocation,
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
            category=self.projectCategory,
            constructionPhaseDetail=self.conPhaseDetail,
            estPlanningStart="2022-11-20",
            estPlanningEnd="2022-11-30",
            estConstructionStart="2022-11-20",
            estConstructionEnd="2022-11-28",
            presenceStart="2022-11-20",
            presenceEnd="2022-11-20",
            visibilityStart="2022-11-20",
            visibilityEnd="2022-11-20",
            perfAmount=20000.00,
            unitCost=10000.00,
            costForecast=10000.00,
            neighborhood="my random neigbhorhood",
            comittedCost=120.0,
            tiedCurrYear=12000.00,
            realizedCost=20.00,
            spentCost=20000.00,
            riskAssessment=None,
            priority=self.projectPriority,
            comments="Comments random",
            delays="yes 1 delay because of tests",
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
            louhi=False,
            gravel=False,
            budget=50,
            budgetGroupPercentage=50,
            planningStartYear="2022",
            constructionEndYear="2030",
            budgetOverrunYear="2030",
            budgetOverrunAmount=50,
            projectWorkQuantity=2,
            projectQualityLevel=self.projectQualityLevel,
            projectCostForecast=20,
            planningCostForecast=20,
            planningWorkQuantity=2,
            planningPhase=self.planningPhase,
            constructionCostForecast=20,
            constructionWorkQuantity=2,
            constructionPhase=self.constructionPhase,
            effectHousing=False,
        )
        self.project.favPersons.add(self.person_1, self.person_2)
        self.project.hashTags.add(self.projectHashTag_1, self.projectHashTag_2)

    def test_project_is_created(self):
        self.assertTrue(
            Project.objects.filter(id=self.project_1_Id).exists(),
            msg="Object does not exist in DB",
        )
        project = Project.objects.get(id=self.project_1_Id)
        self.assertIsInstance(
            project, Project, msg="Object retrieved from DB != typeof Project Model"
        )
        self.assertEqual(project, self.project, msg="Object from DB != created Object")

    def test_project_foreign_keys_exists(self):

        self.assertDictEqual(
            self.budgetItem.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="siteId foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.projectSet.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="projectSet foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.projectArea.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="projectArea foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.projectType.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="projectType foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.projectPhase.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="projectPhase foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.projectPriority.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="projectPriority foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.person_3.construction.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="personConstruction foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.projectLocation.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="projectLocation foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.person_2.planning.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="personPlanning foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.person_1.programming.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="personProgramming foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.projectClass.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="projectClass foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.projectCategory.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="projectCategory foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.conPhaseDetail.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="conPhaseDetail foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )

        self.assertDictEqual(
            self.projectQualityLevel.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="projectQualityLevel foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.planningPhase.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="planningPhase foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )
        self.assertDictEqual(
            self.constructionPhase.project_set.all().values()[0],
            Project.objects.filter(id=self.project_1_Id).values()[0],
            msg="constructionPhase foreign key does not exist in Project with id {}".format(
                self.project_1_Id
            ),
        )

    def test_project_manyTomany_relationship_exists(self):
        person_1_reverse_query = self.person_1.favourite.all().values()[0]
        person_2_reverse_query = self.person_2.favourite.all().values()[0]
        self.assertDictEqual(
            person_1_reverse_query,
            person_2_reverse_query,
            msg="Reverse relationship from manyTomany Person keys do not point to the same Project or does not exist",
        )
        projectHashtag_1_reverse_query = (
            self.projectHashTag_1.relatedProject.all().values()[0]
        )
        projectHashtag_2_reverse_query = (
            self.projectHashTag_2.relatedProject.all().values()[0]
        )
        self.assertDictEqual(
            projectHashtag_1_reverse_query,
            projectHashtag_2_reverse_query,
            msg="Reverse relationship from manyTomany HashTag keys do not point to the same Project or does not exist",
        )

    def test_GET_all_projects(self):
        response = self.client.get("/projects/")
        projectCount = Project.objects.all().count()
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            projectCount,
            msg="Number of retrieved projects is != {}".format(projectCount),
        )
        Project.objects.create(
            id=self.project_2_Id,
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
            constructionPhaseDetail=None,
            estPlanningStart="2022-11-20",
            estPlanningEnd="2022-11-30",
            estConstructionStart="2022-11-20",
            estConstructionEnd="2022-11-28",
            presenceStart="2022-11-20",
            presenceEnd="2022-11-20",
            visibilityStart="2022-11-20",
            visibilityEnd="2022-11-20",
            perfAmount=20000.00,
            unitCost=10000.00,
            costForecast=10000.00,
            neighborhood="my random neigbhorhood 2",
            comittedCost=120.0,
            tiedCurrYear=12000.00,
            realizedCost=20.00,
            spentCost=20000.00,
            riskAssessment=None,
            category=None,
            priority=self.projectPriority,
            comments="Comments random",
            delays="yes 1 delay because of tests",
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
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            projectCount + 1,
            msg="Number of retrieved projects is != {}".format(projectCount + 1),
        )

    def test_GET_one_project(self):
        response = self.client.get(
            "/projects/{}/".format(self.project_1_Id),
        )
        # serialize the model instances
        serializer = ProjectGetSerializer(
            Project.objects.get(id=self.project_1_Id), many=False
        )

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected

        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.content,
            result_expected,
            msg="Project data in response != Project data in DB",
        )

    def test_POST_project(self):
        data = {
            "siteId": None,
            "hkrId": 12345,
            "sapProject": None,
            "sapNetwork": None,
            "projectSet": None,
            "entityName": None,
            "area": None,
            "type": None,
            "name": "Test_POST_PROJECT",
            "address": None,
            "description": "Description of POST project",
            "personPlanning": None,
            "personProgramming": None,
            "personConstruction": None,
            "phase": None,
            "programmed": True,
            "category": None,
            "constructionPhaseDetail": None,
            "estPlanningStart": None,
            "estPlanningEnd": None,
            "estConstructionStart": None,
            "estConstructionEnd": None,
            "presenceStart": None,
            "presenceEnd": None,
            "visibilityStart": None,
            "visibilityEnd": None,
            "perfAmount": None,
            "unitCost": None,
            "costForecast": None,
            "neighborhood": None,
            "comittedCost": None,
            "tiedCurrYear": None,
            "realizedCost": None,
            "spentCost": None,
            "riskAssessment": None,
            "priority": None,
            "comments": None,
            "delays": None,
            "hashTags": None,
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
            "louhi": False,
            "gravel": False,
            "budget": None,
            "budgetGroupPercentage": None,
            "planningStartYear": None,
            "constructionEndYear": None,
            "budgetOverrunYear": None,
            "budgetOverrunAmount": None,
            "projectWorkQuantity": None,
            "projectQualityLevel": None,
            "projectCostForecast": None,
            "planningCostForecast": None,
            "planningWorkQuantity": None,
            "planningPhase": None,
            "constructionCostForecast": None,
            "constructionWorkQuantity": None,
            "constructionPhase": None,
            "effectHousing": False,
            "favPersons": [],
            "hashTags": [],
            "projectLocation": None,
            "projectClass": None,
            "projectProgram": None,
            "responsibleZone": None,
            "bridgeNumber": None,
            "masterPlanAreaNumber": None,
            "trafficPlanNumber": None,
            "projectGroup": None,
            "otherPersons": None,
        }
        response = self.client.post(
            "/projects/",
            data,
            content_type="application/json",
        )
        self.assertEqual(
            response.status_code,
            201,
            msg="Status code != 201 , Error: {}".format(response.json()),
        )
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
            "/projects/{}/".format(self.project_1_Id),
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
        response = self.client.delete("/projects/{}/".format(self.project_1_Id))
        self.assertEqual(
            response.status_code,
            204,
            msg="Error deleting project with Id {}".format(self.project_1_Id),
        )
        self.assertEqual(
            Project.objects.filter(id=self.project_1_Id).exists(),
            False,
            msg="Project with Id {} still exists in DB".format(self.project_1_Id),
        )

    def test_notes_project(self):
        Note.objects.create(
            id=self.noteId,
            content="Test note",
            updatedBy=self.person_1,
            project=self.project,
        )
        response = self.client.get("/projects/{}/notes/".format(self.project_1_Id))
        serializer = ProjectNoteGetSerializer(
            Note.objects.filter(id=self.noteId), many=True
        )

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
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
            "comments": "This comment is    random    ",
            "otherPersons": " john    Doe  Person .",
        }

        validData = {
            "name": "test project. name",
            "address": "Address. works for me.",
            "description": "random Description works. yes",
            "entityName": "Entity Name",
            "delays": "100 delays .",
            "comments": "This comment is random",
            "otherPersons": "John Doe Person.",
        }

        response = self.client.post(
            "/projects/",
            data,
            content_type="application/json",
        )
        self.assertEqual(
            response.status_code,
            201,
            msg="Status code != 201 , Error: {}".format(response.json()),
        )
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
            res_data["comments"],
            validData["comments"],
            msg="Field: comments not trimmed successfully",
        )
        self.assertEqual(
            Project.objects.filter(id=new_createdId).exists(),
            True,
            msg="Project created using POST request does not exist in DB",
        )

    def test_dateField_formatted_project(self):
        data = {
            "name": "Sample name",
            "description": "Sample description",
            "estPlanningStart": "14.01.2022",
            "estPlanningEnd": "14.05.2022",
            "estConstructionStart": "14.02.2022",
            "estConstructionEnd": "14.05.2022",
            "presenceStart": "14.02.2022",
            "presenceEnd": "14.05.2022",
            "visibilityStart": "14.02.2022",
            "visibilityEnd": "14.05.2022",
        }
        response = self.client.post(
            "/projects/",
            data,
            content_type="application/json",
        )
        res_data = response.json()
        self.assertEqual(
            response.status_code,
            201,
            msg="Status code != 201 , Error: {}".format(response.json()),
        )
        self.assertEqual(
            data["estPlanningStart"],
            res_data["estPlanningStart"],
            msg="estPlanningStart format in POST request != format in response",
        )
        self.assertEqual(
            data["estPlanningEnd"],
            res_data["estPlanningEnd"],
            msg="estPlanningEnd format in POST request != format in response",
        )
        self.assertEqual(
            data["estConstructionStart"],
            res_data["estConstructionStart"],
            msg="estConstructionStart format in POST request != format in response",
        )
        self.assertEqual(
            data["estConstructionEnd"],
            res_data["estConstructionEnd"],
            msg="estConstructionEnd format in POST request != format in response",
        )
        self.assertEqual(
            data["presenceStart"],
            res_data["presenceStart"],
            msg="presenceStart format in POST request != format in response",
        )
        self.assertEqual(
            data["presenceEnd"],
            res_data["presenceEnd"],
            msg="presenceEnd format in POST request != format in response",
        )
        self.assertEqual(
            data["visibilityStart"],
            res_data["visibilityStart"],
            msg="visibilityStart format in POST request != format in response",
        )
        self.assertEqual(
            data["visibilityEnd"],
            res_data["visibilityEnd"],
            msg="visibilityEnd format in POST request != format in response",
        )

        # Giving data in other format still returns data in correct format
        data = {
            "name": "Sample name",
            "description": "Sample description",
            "estPlanningStart": "2022-01-15",
            "estPlanningEnd": "2022-05-15",
            "estConstructionStart": "2022-02-15",
            "estConstructionEnd": "2022-05-15",
            "presenceStart": "2022-02-15",
            "presenceEnd": "2022-05-15",
            "visibilityStart": "2022-02-15",
            "visibilityEnd": "2022-05-15",
        }
        formatted_data = {
            "estPlanningStart": "15.01.2022",
            "estPlanningEnd": "15.05.2022",
            "estConstructionStart": "15.02.2022",
            "estConstructionEnd": "15.05.2022",
            "presenceStart": "15.02.2022",
            "presenceEnd": "15.05.2022",
            "visibilityStart": "15.02.2022",
            "visibilityEnd": "15.05.2022",
        }
        response = self.client.post(
            "/projects/",
            data,
            content_type="application/json",
        )
        res_data = response.json()
        self.assertEqual(
            response.status_code,
            201,
            msg="Status code != 201 , Error: {}".format(response.json()),
        )
        self.assertEqual(
            formatted_data["estPlanningStart"],
            res_data["estPlanningStart"],
            msg="estPlanningStart format in POST request != format in response",
        )
        self.assertEqual(
            formatted_data["estPlanningEnd"],
            res_data["estPlanningEnd"],
            msg="estPlanningEnd format in POST request != format in response",
        )
        self.assertEqual(
            formatted_data["estConstructionStart"],
            res_data["estConstructionStart"],
            msg="estConstructionStart format in POST request != format in response",
        )
        self.assertEqual(
            formatted_data["estConstructionEnd"],
            res_data["estConstructionEnd"],
            msg="estConstructionEnd format in POST request != format in response",
        )
        self.assertEqual(
            formatted_data["presenceStart"],
            res_data["presenceStart"],
            msg="presenceStart format in POST request != format in response",
        )
        self.assertEqual(
            formatted_data["presenceEnd"],
            res_data["presenceEnd"],
            msg="presenceEnd format in POST request != format in response",
        )
        self.assertEqual(
            formatted_data["visibilityStart"],
            res_data["visibilityStart"],
            msg="visibilityStart format in POST request != format in response",
        )
        self.assertEqual(
            formatted_data["visibilityEnd"],
            res_data["visibilityEnd"],
            msg="visibilityEnd format in POST request != format in response",
        )

    def test_endpoint_filter_project(self):
        projectGroup_1 = ProjectGroup.objects.create(
            id=self.projectGroup_1_Id, name="Test Group 1 rain"
        )
        projectGroup_2 = ProjectGroup.objects.create(
            id=self.projectGroup_2_Id, name="Test Group 2"
        )
        projectGroup_3 = ProjectGroup.objects.create(
            id=self.projectGroup_3_Id, name="Test Group 3 park"
        )
        mainDistrict_1 = ProjectLocation.objects.create(
            id=self.projectMainDistrict_2_Id,
            name="Main District 1",
            parent=None,
            path="Main District 1",
        )
        mainDistrict_2 = ProjectLocation.objects.create(
            id=self.projectMainDistrict_3_Id,
            name="Main District 2",
            parent=None,
            path="Main District 2",
        )
        district = mainDistrict_1.childLocation.create(
            id=self.projectDistrict_2_Id,
            name="District 1",
            path="Main District 1/District 1",
        )
        subDistrict_1 = district.childLocation.create(
            id=self.projectSubDistrict_1_Id,
            name="Sub district 1",
            path="Main District 1/District 1/Sub district 1",
        )
        subDistrict_2 = district.childLocation.create(
            id=self.projectSubDistrict_2_Id,
            name="Sub district 2",
            path="Main District 1/District 1/Sub district 2",
        )

        category_1 = ProjectCategory.objects.create(
            id=self.projectCategory_2_Id, value="K5"
        )
        category_2 = ProjectCategory.objects.create(
            id=self.projectCategory_3_Id, value="K1"
        )
        masterClass_1 = ProjectClass.objects.create(
            id=self.projectMasterClass_2_Id,
            name="Master Class 1",
            parent=None,
            path="Master Class 1",
        )
        masterClass_2 = ProjectClass.objects.create(
            id=self.projectMasterClass_3_Id,
            name="Master Class 2",
            parent=None,
            path="Master Class 2",
        )
        _class = masterClass_1.childClass.create(
            name="Test Class 1",
            id=self.projectClass_2_Id,
            path="Master Class 1/Test Class 1",
        )
        subClass_1 = _class.childClass.create(
            id=self.projectSubClass_1_Id,
            name="Sub class 1",
            path="Master Class 1/Test Class 1/Sub class 1",
        )
        subClass_2 = _class.childClass.create(
            id=self.projectSubClass_2_Id,
            name="Sub class 2",
            path="Master Class 1/Test Class 1/Sub class 2",
        )
        hashTag_1 = ProjectHashTag.objects.create(
            id=self.projectHashTag_3_Id, value="Jira"
        )
        hashTag_2 = ProjectHashTag.objects.create(
            id=self.projectHashTag_4_Id, value="Park"
        )

        project_1 = Project.objects.create(
            id=self.project_3_Id,
            hkrId=2222,
            name="Parking Helsinki",
            description="Random desc",
            programmed=True,
            category=category_1,
            projectLocation=mainDistrict_1,
            projectClass=subClass_1,
            projectGroup=projectGroup_1,
        )
        project_1.hashTags.add(hashTag_1)
        project_2 = Project.objects.create(
            id=self.project_4_Id,
            hkrId=1111,
            name="Random name",
            description="Random desc",
            programmed=True,
            category=category_2,
            projectLocation=subDistrict_1,
            projectClass=_class,
            projectGroup=projectGroup_1,
        )
        project_2.hashTags.add(hashTag_2)
        project_3 = Project.objects.create(
            id=self.project_5_Id,
            hkrId=3333,
            name="Train Train Bike",
            description="Random desc",
            programmed=False,
            category=category_2,
            projectLocation=mainDistrict_2,
            projectClass=subClass_2,
            projectGroup=projectGroup_2,
        )
        project_3.hashTags.add(hashTag_1, hashTag_2)
        project_4 = Project.objects.create(
            id=self.project_6_Id,
            hkrId=5555,
            name="Futurice Office Jira",
            description="Random desc",
            programmed=False,
            category=category_2,
            projectLocation=subDistrict_2,
            projectClass=masterClass_2,
            projectGroup=projectGroup_3,
        )

        response = self.client.get(
            "/projects/?hkrId={}".format(2222),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            1,
            msg="Filtered result should contain 1 project with hkrId: 2222. Found: {}".format(
                response.json()["count"]
            ),
        )
        response = self.client.get(
            "/projects/?freeSearch={}".format("jira"),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            len(response.json()["projects"]),
            1,
            msg="Filtered result should contain 1 project with the string 'jira' appearing in name field",
        )
        self.assertEqual(
            len(response.json()["hashtags"]),
            1,
            msg="Filtered result should contain 1 hashTag with the string 'jira' appearing in value field",
        )
        self.assertEqual(
            len(response.json()["groups"]),
            0,
            msg="Filtered result should contain 0 groups with the string 'jira' appearing in value field",
        )
        response = self.client.get(
            "/projects/?freeSearch={}".format("park"),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            len(response.json()["hashtags"]),
            1,
            msg="Filtered result should contain 1 hashTag with the string 'park' appearing in value field",
        )
        self.assertEqual(
            len(response.json()["projects"]),
            1,
            msg="Filtered result should contain 1 project with the string 'park' appearing in name field",
        )
        self.assertEqual(
            len(response.json()["groups"]),
            1,
            msg="Filtered result should contain 1 group with the string 'park' appearing in name field",
        )
        response = self.client.get(
            "/projects/?freeSearch={}".format("Parking"),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            len(response.json()["projects"]),
            1,
            msg="Filtered result should contain 1 project with the string 'Parking' appearing in name field",
        )
        self.assertEqual(
            len(response.json()["hashtags"]),
            0,
            msg="Filtered result should contain no hashtags with the string 'Parking' appearing in value field",
        )

        response = self.client.get(
            "/projects/?programmed={}".format("false"),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            2,
            msg="Filtered result should contain 2 projects with field programmed = false. Found: {}".format(
                response.json()["count"]
            ),
        )
        response = self.client.get(
            "/projects/?programmed={}&programmed={}".format("false", "true"),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            Project.objects.all().count(),
            msg="Filtered result should contain all projects existing in the DB",
        )
        response = self.client.get(
            "/projects/?programmed={}&hkrId={}".format("false", "3333"),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            1,
            msg="Filtered result should contain 1 project with field programmed = false and hkrId = 333. Found: {}".format(
                response.json()["count"]
            ),
        )
        response = self.client.get(
            "/projects/?masterClass={}".format(self.projectMasterClass_2_Id),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            3,
            msg="Filtered result should contain 3 projects belonging to masterClass Id: {}, directly or indirectly. Found: {}".format(
                self.projectMasterClass_2_Id, response.json()["count"]
            ),
        )
        response = self.client.get(
            "/projects/?subClass={}&masterClass={}".format(
                self.projectSubClass_2_Id, self.projectMasterClass_3_Id
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            0,
            msg="Filtered result should contain 0 projects with masterClass Id: {} and subClass Id: {}. Found: {}".format(
                self.projectMasterClass_3_Id,
                self.projectSubClass_2_Id,
                response.json()["count"],
            ),
        )
        response = self.client.get(
            "/projects/?subClass={}".format(self.projectSubClass_1_Id),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            1,
            msg="Filtered result should contain 1 project belonging to subClass Id: {}. Found: {}".format(
                self.projectSubClass_1_Id, response.json()["count"]
            ),
        )
        response = self.client.get(
            "/projects/?subClass={}&subClass={}".format(
                self.projectSubClass_1_Id, self.projectSubClass_2_Id
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            2,
            msg="Filtered result should contain a project belonging to subClass Id: {} and another belonging to subClass Id: {}. Found: {}".format(
                self.projectSubClass_1_Id,
                self.projectSubClass_2_Id,
                response.json()["count"],
            ),
        )

        response = self.client.get(
            "/projects/?subClass={}&category={}".format(
                self.projectSubClass_2_Id, self.projectCategory_3_Id
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            1,
            msg="Filtered result should contain a project belonging to subClass Id: {} and category Id: {}. Found: {}".format(
                self.projectSubClass_2_Id,
                self.projectCategory_3_Id,
                response.json()["count"],
            ),
        )
        response = self.client.get(
            "/projects/?class={}".format(self.projectClass_2_Id),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            3,
            msg="Filtered result should contain 3 projects belonging to class Id: {}, directly or indirectly. Found: {}".format(
                self.projectClass_2_Id,
                response.json()["count"],
            ),
        )

        response = self.client.get(
            "/projects/?mainDistrict={}".format(self.projectMainDistrict_2_Id),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            3,
            msg="Filtered result should contain 3 projects belonging to mainDistrict Id: {}, directly or indirectly. Found: {}".format(
                self.projectMainDistrict_2_Id, response.json()["count"]
            ),
        )
        response = self.client.get(
            "/projects/?mainDistrict={}&hashtags={}".format(
                self.projectMainDistrict_3_Id, self.projectHashTag_3_Id
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            1,
            msg="Filtered result should contain 1 project belonging to mainDistrict Id: {}, directly or indirectly, \
                with the hashTag: {} . Found: {}".format(
                self.projectMainDistrict_3_Id,
                self.projectHashTag_3_Id,
                response.json()["count"],
            ),
        )
        response = self.client.get(
            "/projects/?mainDistrict={}&mainDistrict={}".format(
                self.projectMainDistrict_2_Id, self.projectMainDistrict_3_Id
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            4,
            msg="Filtered result should contain 4 projects belonging to mainDistrict Id: {} or {}, directly or indirectly. Found: {}".format(
                self.projectMainDistrict_2_Id,
                self.projectMainDistrict_3_Id,
                response.json()["count"],
            ),
        )
        response = self.client.get(
            "/projects/?mainDistrict={}&programmed={}".format(
                self.projectMainDistrict_3_Id, "false"
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            1,
            msg="Filtered result should contain 1 project belonging to mainDistrict Id: {}, directly or indirectly, and field programmed = false. Found: {}".format(
                self.projectMainDistrict_3_Id,
                response.json()["count"],
            ),
        )
        response = self.client.get(
            "/projects/?masterClass={}&subClass={}".format(
                self.projectMasterClass_2_Id, self.projectSubClass_2_Id
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            1,
            msg="Filtered result should contain 1 project belonging to masterClass Id: {}, directly or indirectly, and field programmed = false. Found: {}".format(
                self.projectMasterClass_2_Id,
                response.json()["count"],
            ),
        )
        response = self.client.get(
            "/projects/?programmed={}&category={}".format(
                "true", self.projectCategory_3_Id
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            1,
            msg="Filtered result should contain 1 project with field programmed = true and category Id: {}. Found: {}".format(
                self.projectCategory_3_Id, response.json()["count"]
            ),
        )
        response = self.client.get(
            "/projects/?masterClass={}&masterClass={}&subClass={}&subClass={}".format(
                self.projectMasterClass_2_Id,
                self.projectMasterClass_3_Id,
                self.projectSubClass_1_Id,
                self.projectSubClass_2_Id,
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            2,
            msg="Filtered result should contain 2 projects belonging to masterClass Id: {}, directly or indirectly, and subClass Id: {} or {} each. Found: {}".format(
                self.projectMasterClass_2_Id,
                self.projectSubClass_1_Id,
                self.projectSubClass_2_Id,
                response.json()["count"],
            ),
        )
        response = self.client.get(
            "/projects/?hashTags={}".format(self.projectHashTag_3_Id),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )

        self.assertEqual(
            response.json()["count"],
            2,
            msg="Filtered result should contain 2 projects with hashTag: {}. Found: {}".format(
                self.projectHashTag_3_Id,
                response.json()["count"],
            ),
        )

        response = self.client.get(
            "/projects/?hashTags={}&hashTags={}".format(
                self.projectHashTag_3_Id, self.projectHashTag_4_Id
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            response.json()["count"],
            3,
            msg="Filtered result should contain 3 projects with hashTag: {} or {}. Found: {}".format(
                self.projectHashTag_3_Id,
                self.projectHashTag_4_Id,
                response.json()["count"],
            ),
        )

        response = self.client.get(
            "/projects/?hashTags={}&hashTags={}&projectGroup={}".format(
                self.projectHashTag_3_Id,
                self.projectHashTag_4_Id,
                self.projectGroup_1_Id,
            ),
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )

        self.assertEqual(
            response.json()["count"],
            2,
            msg="Filtered result should contain 2 projects with hashTag: {} or {} and group: {}. Found: {}".format(
                self.projectHashTag_3_Id,
                self.projectHashTag_4_Id,
                self.projectGroup_1_Id,
                response.json()["count"],
            ),
        )

    def test_project_gets_locked(self):
        ProjectPhase.objects.create(id=self.projectPhase_2_Id, value="construction")
        data = {
            "name": "Test locking",
            "description": "Test Description",
            "phase": self.projectPhase_2_Id.__str__(),
        }
        response = self.client.post(
            "/projects/",
            data,
            content_type="application/json",
        )
        newCreatedId = response.json()["id"]
        self.assertEqual(
            response.status_code,
            201,
            msg="Status code != 201 , Error: {}".format(response.json()),
        )
        self.assertTrue(
            ProjectLock.objects.filter(project=newCreatedId).exists(),
            msg="ProjectLock does not contain a record for new created project with id {} when phase is set to construction".format(
                newCreatedId
            ),
        )

        data["phase"] = self.projectPhase_1_Id.__str__()
        response = self.client.post(
            "/projects/",
            data,
            content_type="application/json",
        )
        newCreatedId = response.json()["id"]
        self.assertEqual(
            response.status_code,
            201,
            msg="Status code != 200 , Error: {}".format(response.json()),
        )
        self.assertFalse(
            ProjectLock.objects.filter(project=newCreatedId).exists(),
            msg="ProjectLock contains a record for new created project with id {} when phase is not set to construction".format(
                newCreatedId
            ),
        )

        data["phase"] = self.projectPhase_2_Id.__str__()
        response = self.client.patch(
            "/projects/{}/".format(newCreatedId),
            data,
            content_type="application/json",
        )
        self.assertTrue(
            ProjectLock.objects.filter(project=newCreatedId).exists(),
            msg="ProjectLock does not contain a record for updated project with id {} when phase is updated to construction".format(
                newCreatedId
            ),
        )

    # TODO
    # Define test for updating certain fields when project is locked
    # Define test for locking a project manually
    # Define test for locking a already locked project
