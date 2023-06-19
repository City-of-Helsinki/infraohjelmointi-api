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
    ProjectFinancial,
)
from ..serializers import (
    ProjectGetSerializer,
    ProjectNoteGetSerializer,
    ProjectCreateSerializer,
)
from datetime import date

from rest_framework.renderers import JSONRenderer
from overrides import override


class ProjectTestCase(TestCase):
    project_1_Id = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")
    project_2_Id = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    project_3_Id = uuid.UUID("fdc89f56-b631-4109-a137-45b950de6b10")
    project_4_Id = uuid.UUID("7c5b981e-286f-4065-9d9e-29d8d1714e4c")
    project_5_Id = uuid.UUID("441d80e1-9ab1-4b35-91cc-6017ea308d87")
    project_6_Id = uuid.UUID("90852adc-d47e-4fd9-944f-cb8d36076c21")
    project_7_Id = uuid.UUID("e98e3787-e19f-4af6-94c9-12c8e31ea040")
    project_8_Id = uuid.UUID("3d438292-a7c1-4ef2-9d28-048d580ab2fc")
    project_9_Id = uuid.UUID("a5899694-c5b1-44af-949f-dad9bd06f1a4")
    project_10_Id = uuid.UUID("77da3264-12f2-4abd-a4cd-0992c8f270e6")
    budgetItemId = uuid.UUID("5b1b127f-b4c4-4bea-b994-b2c5c04332f8")
    person_1_Id = uuid.UUID("2c6dece3-cf93-45ba-867d-8f1dd14923fc")
    person_2_Id = uuid.UUID("7fe92cae-d866-4e12-b182-547c367efe12")
    person_3_Id = uuid.UUID("b56ae8c8-f5c2-4abe-a1a6-f3a83265ff49")
    person_4_Id = uuid.UUID("2b8ffec5-de77-498c-afe7-a1999a7b2c7c")
    person_5_Id = uuid.UUID("4cd7d70d-2bf2-41bd-998d-be4955cd2a72")
    person_6_Id = uuid.UUID("6af5983a-584e-4b7e-87ed-afc7fc419b2d")
    person_7_Id = uuid.UUID("657f1685-ab79-4997-98a3-d238d60bae1e")
    projectSetId = uuid.UUID("fb093e0e-0b35-4b0e-94d7-97c91997f2d0")
    projectAreaId = uuid.UUID("9acb1ac2-259e-4300-8cf0-f89c3adaf577")
    projectPhase_1_Id = uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256")
    projectPhase_2_Id = uuid.UUID("562e3d4f-77ac-4b0c-a82a-4b5bff8daa74")
    projectPhase_3_Id = uuid.UUID("2887068f-011a-42bc-a917-d0256f967da0")
    projectPhase_4_Id = uuid.UUID("5a97f844-fdd1-4d50-87a6-e90852a42b2b")
    projectPhase_5_Id = uuid.UUID("644dcdc5-f12f-4cc2-b80f-f64ec649f23c")
    projectPhase_6_Id = uuid.UUID("56fcb6f6-caa9-4d2e-b936-3a5d9261b665")
    projectPhase_7_Id = uuid.UUID("7281620d-bbf1-4411-b541-c72927b39592")
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
    conPhaseDetail_1_Id = uuid.UUID("a7517b59-40f2-4b7d-a146-eef1a3d08c03")
    conPhaseDetail_2_Id = uuid.UUID("9db2b01c-8a1f-42ec-8c21-257b471ed2f5")
    projectQualityLevelId = uuid.UUID("05eb79f5-18c3-40a4-b5c4-22c68a216dec")
    planningPhaseId = uuid.UUID("78570e7c-58b8-4d08-a341-a6c95ad58fed")
    constructionPhaseId = uuid.UUID("c37576af-accf-46aa-8df2-5724ff8a06af")
    projectClass_1_Id = uuid.UUID("5f65a339-b3c9-48ee-a9b9-cb177546c241")
    projectClass_2_Id = uuid.UUID("c03b41d4-bb50-4bc5-ada1-496f399eb157")
    projectClass_3_Id = uuid.UUID("dacd6429-0f60-4ef9-8c9e-54e2a159c8da")
    projectSubClass_1_Id = uuid.UUID("88006f5b-339d-4859-9903-25494deebeca")
    projectSubClass_2_Id = uuid.UUID("48e201a9-7579-42fe-9970-2c0704bd7257")
    projectSubClass_3_Id = uuid.UUID("fe77dce9-56ec-4642-a011-5b611ff879d6")
    projectSubClass_4_Id = uuid.UUID("bdcc6c20-6535-4cc2-9b7e-fa4756cb76e0")
    projectSubClass_5_Id = uuid.UUID("2e147a96-bfee-4a0e-9d44-4095b3c36bdf")
    projectSubClass_6_Id = uuid.UUID("718f7e0e-0dc9-4456-a071-29a8a99437ca")
    projectMasterClass_1_Id = uuid.UUID("78570e7c-58b8-4d08-a341-a6c95ad58fed")
    projectMasterClass_2_Id = uuid.UUID("073e1dee-9e77-4ddd-8d0c-ad856c51e857")
    projectMasterClass_3_Id = uuid.UUID("a66db3fa-eb71-42dc-b618-9e4fae0db8bc")
    projectMasterClass_4_Id = uuid.UUID("b723201e-10c2-40f0-b031-c0e8c072ad7e")
    projectHashTag_1_Id = uuid.UUID("e4d7b4b0-830d-4310-8b29-3c7d1e3132ba")
    projectHashTag_2_Id = uuid.UUID("eb8635b3-4e83-45d9-a1af-6bc49bf2aeb7")
    projectHashTag_3_Id = uuid.UUID("aba0e241-0a02-48a0-8426-e4f034c5f527")
    projectHashTag_4_Id = uuid.UUID("5057f0e5-bdcd-4278-a433-74db4ee34b4b")
    projectDistrict_1_Id = uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256")
    projectDistrict_2_Id = uuid.UUID("740d6771-442b-4713-8362-8bda3958100e")
    projectDistrict_3_Id = uuid.UUID("019eb15d-cfdb-45bc-b1a5-ac3844381e48")
    projectDistrict_4_Id = uuid.UUID("bdd24b4a-ac64-4f49-a979-b2931ac18c8f")
    projectDistrict_5_Id = uuid.UUID("1055e80a-9e2c-4a29-a76a-97528581ff11")
    projectDistrict_6_Id = uuid.UUID("17190fd9-9727-4f3e-a7de-74f682e26a33")
    projectDistrict_7_Id = uuid.UUID("b69e4208-83c6-40bb-854f-4519b3841f66")
    projectDivision_1_Id = uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166")
    projectDivision_2_Id = uuid.UUID("e8f68255-5111-4ab5-b346-016956c671d1")
    projectDivision_3_Id = uuid.UUID("e4864b42-0002-42c6-a0fb-113638810278")
    projectDivision_4_Id = uuid.UUID("0e9e1253-cfe2-405e-9cf4-832a5c5185ac")
    projectDivision_5_Id = uuid.UUID("070e480a-3a50-49dc-bc12-58651f2c7fa4")
    projectDivision_6_Id = uuid.UUID("8aea2fe2-0d74-49c1-a7a0-8a080755a8b8")
    projectSubDivision_1_Id = uuid.UUID("191f9acf-e387-4307-93db-b9f252ec18ff")
    projectSubDivision_2_Id = uuid.UUID("99c4a023-b246-4b1c-be49-848b82b12095")
    projectSubDivision_3_Id = uuid.UUID("b76b3107-628c-4f3e-a2e1-230439da090f")
    projectGroup_1_Id = uuid.UUID("bbba45f2-b0d4-4297-b0e2-4e60f8fa8412")
    projectGroup_2_Id = uuid.UUID("bee657d4-a2cc-4c04-a75b-edc12275dd62")
    projectGroup_3_Id = uuid.UUID("b2e2808c-831b-4db2-b0a8-f6c6d270af1a")
    projectFinancial_1_Id = uuid.UUID("0ace4e90-4318-4282-8bb7-a0b152888642")
    projectFinancial_2_Id = uuid.UUID("ec17c3c6-7414-4fec-ad2e-6e6f63a88bcb")
    projectFinancial_3_Id = uuid.UUID("8dba8690-11fd-4715-9978-f65c4e9a6e22")
    pwInstanceId = "d4a5e51c-2aa5-449a-aa13-a362eb578fd6"
    pwInstanceId_hkrId_1 = 1461
    pwInstanceId_hkrId_2 = 1500
    pwInstanceId_hkrId_1_folder = "pw://HELS000601.helsinki1.hki.local:PWHKIKOUL/Documents/P{d4a5e51c-2aa5-449a-aa13-a362eb578fd6}/"
    pwInstanceId_hkrId_2_folder = "pw://HELS000601.helsinki1.hki.local:PWHKIKOUL/Documents/P{9d14d060-56c8-45c0-9323-303ab440e652}/"

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
        self.district = ProjectLocation.objects.create(
            id=self.projectDistrict_1_Id, name="Test main district", parent=None
        )
        self.projectLocation = self.district.childLocation.create(
            id=self.projectDivision_1_Id, name="Test district"
        )
        self.projectCategory = ProjectCategory.objects.create(
            id=self.projectCategory_1_Id, value="K5"
        )
        self.projectMasterClass = ProjectClass.objects.create(
            id=self.projectMasterClass_1_Id,
            name="Test Master Class",
            parent=None,
            path="Test Master Class",
        )
        self.projectClass = self.projectMasterClass.childClass.create(
            name="Test Class",
            id=self.projectClass_1_Id,
            path="Test Master Class/Test Class",
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
            id=self.conPhaseDetail_1_Id, value="preConstruction"
        )
        self.person_3 = Person.objects.create(
            id=self.person_3_Id,
            firstName="John",
            lastName="Doe 3",
            email="random@random.com",
            title="Contractor",
            phone="0414853275",
        )
        self.projectPhase = ProjectPhase.objects.get(value="proposal")
        self.projectPhase_1_Id = self.projectPhase.id
        self.projectSet = ProjectSet.objects.create(
            id=self.projectSetId,
            name="Project Set 1",
            hkrId=324,
            description="This is test project Set 1",
            responsiblePerson=self.person_2,
            phase=self.projectPhase,
            programmed=True,
        )
        self.projectArea, _ = ProjectArea.objects.get_or_create(
            id=self.projectAreaId,
            value="honkasuo",
            location="inisnoorinkatu 60c",
        )
        self.projectType, _ = ProjectType.objects.get_or_create(
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
            programmed=False,
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

        response = self.client.get("/projects/?limit=1")
        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            len(response.json()["results"]),
            1,
            msg="Number of projects in response != 1",
        )

        response = self.client.get("/projects/?year=2025")
        # serialize the model instances
        serializer = ProjectGetSerializer(
            Project.objects.all(), many=True, context={"finance_year": 2025}
        )

        self.assertEqual(
            response.status_code,
            200,
            msg="Status code != 200, Error: {}".format(response.json()),
        )
        self.assertEqual(
            set([2025]),
            set(project["finances"]["year"] for project in response.json()["results"]),
            msg="Project Data in response must have the financial data from year 2025",
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
            "budgetProposalCurrentYearPlus0": None,
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

        res_data = response.json()
        new_createdId = res_data["id"]
        serializer = ProjectCreateSerializer(
            Project.objects.get(id=new_createdId), many=False
        )

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)
        self.assertEqual(
            response.content, result_expected, msg="Created object data != POST data"
        )
        self.assertEqual(
            Project.objects.filter(id=new_createdId).exists(),
            True,
            msg="Project created using POST request does not exist in DB",
        )

    def test_PATCH_project(self):
        data = {
            "name": "Test Project 1 patched",
            "favPersons": [self.person_1.id.__str__(), self.person_3.id.__str__()],
            "phase": self.projectPhase_1_Id,
        }
        response = self.client.patch(
            "/projects/{}/".format(self.project_1_Id),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, msg=response.json())
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

    def test_PATCH_multiple_projects(self):
        data = {"name": "Test name", "description": "Test description"}
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

        res_data = response.json()
        new_createdId = res_data["id"]

        data = [
            {"id": self.project_1_Id.__str__(), "data": {"name": "new name"}},
            {
                "id": new_createdId,
                "data": {
                    "description": "new description",
                    "finances": {
                        "budgetProposalCurrentYearPlus1": 200,
                        "budgetProposalCurrentYearPlus0": 2,
                        "year": 2025,
                    },
                },
            },
        ]
        response = self.client.patch(
            "/projects/bulk-update/",
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.json()),
            2,
            msg="Response must contain 2 updated projects",
        )
        self.assertEqual(
            response.json()[0]["id"],
            data[0]["id"],
        )
        self.assertEqual(
            response.json()[0]["name"],
            data[0]["data"]["name"],
        )
        self.assertEqual(
            response.json()[1]["id"],
            data[1]["id"],
        )
        self.assertEqual(
            response.json()[1]["description"],
            data[1]["data"]["description"],
        )

        self.assertEqual(
            response.json()[1]["finances"]["year"],
            2025,
        )
        self.assertEqual(
            response.json()[1]["finances"]["budgetProposalCurrentYearPlus1"],
            "200.00",
        )
        self.assertEqual(
            response.json()[1]["finances"]["budgetProposalCurrentYearPlus0"],
            "2.00",
        )

    # def test_DELETE_project(self):
    #     response = self.client.delete("/projects/{}/".format(self.project_1_Id))
    #     self.assertEqual(
    #         response.status_code,
    #         204,
    #         msg="Error deleting project with Id {}".format(self.project_1_Id),
    #     )
    #     self.assertEqual(
    #         Project.objects.filter(id=self.project_1_Id).exists(),
    #         False,
    #         msg="Project with Id {} still exists in DB".format(self.project_1_Id),
    #     )

    # def test_notes_project(self):
    #     Note.objects.create(
    #         id=self.noteId,
    #         content="Test note",
    #         updatedBy=self.person_1,
    #         project=self.project,
    #     )
    #     response = self.client.get("/projects/{}/notes/".format(self.project_1_Id))
    #     serializer = ProjectNoteGetSerializer(
    #         Note.objects.filter(id=self.noteId), many=True
    #     )

    #     # convert the serialized data to JSON
    #     result_expected = JSONRenderer().render(serializer.data)

    #     # compare the JSON data returned to what is expected
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         response.content,
    #         result_expected,
    #         msg="Note data in response != Note data in DB",
    #     )

    # def test_string_sanitization_project(self):
    #     data = {
    #         "name": "   test      project.  name   ",
    #         "address": "  Address.    works   for me.",
    #         "description": " random Description   works.  yes    ",
    #         "entityName": "Entity Name",
    #         "delays": "    100 delays   .",
    #         "comments": "This comment is    random    ",
    #         "otherPersons": " john    Doe  Person .",
    #     }

    #     validData = {
    #         "name": "test project. name",
    #         "address": "Address. works for me.",
    #         "description": "random Description works. yes",
    #         "entityName": "Entity Name",
    #         "delays": "100 delays .",
    #         "comments": "This comment is random",
    #         "otherPersons": "John Doe Person.",
    #     }

    #     response = self.client.post(
    #         "/projects/",
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         201,
    #         msg="Status code != 201 , Error: {}".format(response.json()),
    #     )
    #     # deleting id because request body doesn't contain an id and
    #     #  but the response does if new resource is created
    #     res_data = response.json()
    #     new_createdId = res_data["id"]
    #     del res_data["id"]
    #     self.assertEqual(
    #         res_data["name"],
    #         validData["name"],
    #         msg="Field: name not trimmed successfully",
    #     )
    #     self.assertEqual(
    #         res_data["address"],
    #         validData["address"],
    #         msg="Field: address not trimmed successfully",
    #     )
    #     self.assertEqual(
    #         res_data["description"],
    #         validData["description"],
    #         msg="Field: description not trimmed successfully",
    #     )
    #     self.assertEqual(
    #         res_data["entityName"],
    #         validData["entityName"],
    #         msg="Field: entityName not trimmed successfully",
    #     )
    #     self.assertEqual(
    #         res_data["delays"],
    #         validData["delays"],
    #         msg="Field: delays not trimmed successfully",
    #     )
    #     self.assertEqual(
    #         res_data["comments"],
    #         validData["comments"],
    #         msg="Field: comments not trimmed successfully",
    #     )
    #     self.assertEqual(
    #         Project.objects.filter(id=new_createdId).exists(),
    #         True,
    #         msg="Project created using POST request does not exist in DB",
    #     )

    # def test_dateField_formatted_project(self):
    #     data = {
    #         "name": "Sample name",
    #         "description": "Sample description",
    #         "estPlanningStart": "14.01.2022",
    #         "estPlanningEnd": "14.05.2022",
    #         "estConstructionStart": "20.05.2022",
    #         "estConstructionEnd": "01.06.2022",
    #         "presenceStart": "14.02.2022",
    #         "presenceEnd": "14.05.2022",
    #         "visibilityStart": "14.02.2022",
    #         "visibilityEnd": "14.05.2022",
    #     }
    #     response = self.client.post(
    #         "/projects/",
    #         data,
    #         content_type="application/json",
    #     )
    #     res_data = response.json()
    #     self.assertEqual(
    #         response.status_code,
    #         201,
    #         msg="Status code != 201 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         data["estPlanningStart"],
    #         res_data["estPlanningStart"],
    #         msg="estPlanningStart format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         data["estPlanningEnd"],
    #         res_data["estPlanningEnd"],
    #         msg="estPlanningEnd format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         data["estConstructionStart"],
    #         res_data["estConstructionStart"],
    #         msg="estConstructionStart format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         data["estConstructionEnd"],
    #         res_data["estConstructionEnd"],
    #         msg="estConstructionEnd format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         data["presenceStart"],
    #         res_data["presenceStart"],
    #         msg="presenceStart format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         data["presenceEnd"],
    #         res_data["presenceEnd"],
    #         msg="presenceEnd format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         data["visibilityStart"],
    #         res_data["visibilityStart"],
    #         msg="visibilityStart format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         data["visibilityEnd"],
    #         res_data["visibilityEnd"],
    #         msg="visibilityEnd format in POST request != format in response",
    #     )

    #     # Giving data in other format still returns data in correct format
    #     data = {
    #         "name": "Sample name",
    #         "description": "Sample description",
    #         "estPlanningStart": "2022-01-15",
    #         "estPlanningEnd": "2022-05-15",
    #         "estConstructionStart": "2022-06-15",
    #         "estConstructionEnd": "2022-08-15",
    #         "presenceStart": "2022-02-15",
    #         "presenceEnd": "2022-05-15",
    #         "visibilityStart": "2022-02-15",
    #         "visibilityEnd": "2022-05-15",
    #     }
    #     formatted_data = {
    #         "estPlanningStart": "15.01.2022",
    #         "estPlanningEnd": "15.05.2022",
    #         "estConstructionStart": "15.06.2022",
    #         "estConstructionEnd": "15.08.2022",
    #         "presenceStart": "15.02.2022",
    #         "presenceEnd": "15.05.2022",
    #         "visibilityStart": "15.02.2022",
    #         "visibilityEnd": "15.05.2022",
    #     }
    #     response = self.client.post(
    #         "/projects/",
    #         data,
    #         content_type="application/json",
    #     )
    #     res_data = response.json()
    #     self.assertEqual(
    #         response.status_code,
    #         201,
    #         msg="Status code != 201 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         formatted_data["estPlanningStart"],
    #         res_data["estPlanningStart"],
    #         msg="estPlanningStart format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         formatted_data["estPlanningEnd"],
    #         res_data["estPlanningEnd"],
    #         msg="estPlanningEnd format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         formatted_data["estConstructionStart"],
    #         res_data["estConstructionStart"],
    #         msg="estConstructionStart format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         formatted_data["estConstructionEnd"],
    #         res_data["estConstructionEnd"],
    #         msg="estConstructionEnd format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         formatted_data["presenceStart"],
    #         res_data["presenceStart"],
    #         msg="presenceStart format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         formatted_data["presenceEnd"],
    #         res_data["presenceEnd"],
    #         msg="presenceEnd format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         formatted_data["visibilityStart"],
    #         res_data["visibilityStart"],
    #         msg="visibilityStart format in POST request != format in response",
    #     )
    #     self.assertEqual(
    #         formatted_data["visibilityEnd"],
    #         res_data["visibilityEnd"],
    #         msg="visibilityEnd format in POST request != format in response",
    #     )

    # def test_search_results_endpoint_project(self):
    #     projectGroup_1 = ProjectGroup.objects.create(
    #         id=self.projectGroup_1_Id, name="Test Group 1 rain"
    #     )
    #     projectGroup_2 = ProjectGroup.objects.create(
    #         id=self.projectGroup_2_Id, name="Test Group 2"
    #     )
    #     projectGroup_3 = ProjectGroup.objects.create(
    #         id=self.projectGroup_3_Id, name="Test Group 3 park"
    #     )
    #     district_1 = ProjectLocation.objects.create(
    #         id=self.projectDistrict_2_Id,
    #         name="District 1",
    #         parent=None,
    #         path="District 1",
    #     )
    #     district_2 = ProjectLocation.objects.create(
    #         id=self.projectDistrict_3_Id,
    #         name="District 2",
    #         parent=None,
    #         path="District 2",
    #     )
    #     division = district_1.childLocation.create(
    #         id=self.projectDivision_2_Id,
    #         name="District 1",
    #         path="District 1/Division 1",
    #     )
    #     subDivision_1 = division.childLocation.create(
    #         id=self.projectSubDivision_1_Id,
    #         name="SubDivision 1",
    #         path="District 1/Division 1/SubDivision 1",
    #     )
    #     subDivision_2 = division.childLocation.create(
    #         id=self.projectSubDivision_2_Id,
    #         name="SubDivision 2",
    #         path="District 1/Division 1/SubDivision 2",
    #     )

    #     category_1 = ProjectCategory.objects.create(
    #         id=self.projectCategory_2_Id, value="K5"
    #     )
    #     category_2 = ProjectCategory.objects.create(
    #         id=self.projectCategory_3_Id, value="K1"
    #     )
    #     masterClass_1 = ProjectClass.objects.create(
    #         id=self.projectMasterClass_2_Id,
    #         name="Master Class 1",
    #         parent=None,
    #         path="Master Class 1",
    #     )
    #     masterClass_2 = ProjectClass.objects.create(
    #         id=self.projectMasterClass_3_Id,
    #         name="Master Class 2",
    #         parent=None,
    #         path="Master Class 2",
    #     )
    #     _class = masterClass_1.childClass.create(
    #         name="Test Class 1",
    #         id=self.projectClass_2_Id,
    #         path="Master Class 1/Test Class 1",
    #     )
    #     subClass_1 = _class.childClass.create(
    #         id=self.projectSubClass_1_Id,
    #         name="Sub class 1",
    #         path="Master Class 1/Test Class 1/Sub class 1",
    #     )
    #     subClass_2 = _class.childClass.create(
    #         id=self.projectSubClass_2_Id,
    #         name="Sub class 2",
    #         path="Master Class 1/Test Class 1/Sub class 2",
    #     )
    #     hashTag_1 = ProjectHashTag.objects.create(
    #         id=self.projectHashTag_3_Id, value="Jira"
    #     )
    #     hashTag_2 = ProjectHashTag.objects.create(
    #         id=self.projectHashTag_4_Id, value="Park"
    #     )
    #     personPlanning = Person.objects.create(
    #         id=self.person_4_Id,
    #         firstName="Person",
    #         lastName="Test",
    #         email="random@random.com",
    #         title="Planning",
    #         phone="0414853275",
    #     )

    #     project_1 = Project.objects.create(
    #         id=self.project_3_Id,
    #         hkrId=2222,
    #         name="Parking Helsinki",
    #         description="Random desc",
    #         programmed=True,
    #         category=category_1,
    #         projectLocation=district_1,
    #         projectClass=subClass_1,
    #         projectGroup=projectGroup_1,
    #         personPlanning=personPlanning,
    #     )
    #     project_1.hashTags.add(hashTag_1)
    #     project_2 = Project.objects.create(
    #         id=self.project_4_Id,
    #         hkrId=1111,
    #         name="Random name",
    #         description="Random desc",
    #         programmed=True,
    #         category=category_2,
    #         projectLocation=subDivision_1,
    #         projectClass=_class,
    #         projectGroup=projectGroup_1,
    #         personPlanning=personPlanning,
    #     )
    #     project_2.hashTags.add(hashTag_2)
    #     project_3 = Project.objects.create(
    #         id=self.project_5_Id,
    #         hkrId=3333,
    #         name="Train Train Bike",
    #         description="Random desc",
    #         programmed=False,
    #         category=category_2,
    #         projectLocation=district_2,
    #         projectClass=subClass_2,
    #         projectGroup=projectGroup_2,
    #     )
    #     project_3.hashTags.add(hashTag_1, hashTag_2)

    #     project_4 = Project.objects.create(
    #         id=self.project_6_Id,
    #         hkrId=5555,
    #         name="Futurice Office Jira",
    #         description="Random desc",
    #         programmed=False,
    #         category=category_2,
    #         projectLocation=subDivision_2,
    #         projectClass=masterClass_2,
    #         projectGroup=projectGroup_3,
    #         personPlanning=personPlanning,
    #     )
    #     Project.objects.create(
    #         id=self.project_10_Id,
    #         hkrId=1111,
    #         name="Random name",
    #         description="Random desc",
    #         programmed=True,
    #         category=category_2,
    #         projectClass=_class,
    #         projectGroup=projectGroup_1,
    #         personPlanning=personPlanning,
    #     )
    #     projectFinances_1 = ProjectFinancial.objects.create(
    #         project=project_1,
    #         budgetProposalCurrentYearPlus0=10.00,
    #         budgetProposalCurrentYearPlus1=20.00,
    #         budgetProposalCurrentYearPlus2=30.00,
    #         preliminaryCurrentYearPlus3=40.00,
    #         preliminaryCurrentYearPlus4=5.00,
    #         preliminaryCurrentYearPlus5=0.00,
    #         preliminaryCurrentYearPlus6=0.00,
    #         preliminaryCurrentYearPlus7=0.00,
    #         preliminaryCurrentYearPlus8=0.00,
    #         preliminaryCurrentYearPlus9=0.00,
    #         preliminaryCurrentYearPlus10=0.00,
    #     )
    #     projectFinances_2 = ProjectFinancial.objects.create(
    #         project=project_2,
    #         budgetProposalCurrentYearPlus0=0.00,
    #         budgetProposalCurrentYearPlus1=0.00,
    #         budgetProposalCurrentYearPlus2=50.00,
    #         preliminaryCurrentYearPlus3=40.00,
    #         preliminaryCurrentYearPlus4=5.00,
    #         preliminaryCurrentYearPlus5=0.00,
    #         preliminaryCurrentYearPlus6=0.00,
    #         preliminaryCurrentYearPlus7=5.00,
    #         preliminaryCurrentYearPlus8=9.00,
    #         preliminaryCurrentYearPlus9=10.00,
    #         preliminaryCurrentYearPlus10=0.00,
    #     )

    #     projectFinances_3 = ProjectFinancial.objects.create(
    #         project=project_3,
    #         budgetProposalCurrentYearPlus0=0.00,
    #         budgetProposalCurrentYearPlus1=0.00,
    #         budgetProposalCurrentYearPlus2=50.00,
    #         preliminaryCurrentYearPlus3=40.00,
    #         preliminaryCurrentYearPlus4=5.00,
    #         preliminaryCurrentYearPlus5=0.00,
    #         preliminaryCurrentYearPlus6=0.00,
    #         preliminaryCurrentYearPlus7=5.00,
    #         preliminaryCurrentYearPlus8=9.00,
    #         preliminaryCurrentYearPlus9=10.00,
    #         preliminaryCurrentYearPlus10=0.00,
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?prYearMin={}".format(2025),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         2,
    #         msg="Filtered result should contain 2 projects with financial fields related to year >= 2025 with values > 0 and programmed = true. Found: {}".format(
    #             len(response.json()["results"])
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?prYearMin={}".format(2030),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         1,
    #         msg="Filtered result should contain 1 projects with financial fields related to year >= 2030 with values > 0 and programmed = true. Found: {}".format(
    #             len(response.json()["results"])
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?prYearMax={}".format(2024),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         1,
    #         msg="Filtered result should contain 1 projects with financial fields related to year <= 2024 with values > 0 and programmed = true. Found: {}".format(
    #             len(response.json()["results"])
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?prYearMin={}&prYearMax={}".format(2030, 2032),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         1,
    #         msg="Filtered result should contain 1 project with financial fields > 0 for years in range 2030-2032 and programmed = true. Found: {}".format(
    #             len(response.json()["results"])
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?prYearMin={}&prYearMax={}".format(2030, 2032),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         1,
    #         msg="Filtered result should contain 1 project with financial fields > 0 for years in range 2030-2032 and programmed = true. Found: {}".format(
    #             len(response.json()["results"])
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?prYearMin={}&prYearMax={}".format(2028, 2029),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         0,
    #         msg="Filtered result should contain 0 project with financial fields > 0 for years in range 2028-2029 and programmed = true. Found: {}".format(
    #             len(response.json()["results"])
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?hkrId={}".format(2222),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         1,
    #         msg="Filtered result should contain 1 project with hkrId: 2222. Found: {}".format(
    #             len(response.json()["results"])
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?freeSearch={}".format("jira"),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project with the string 'jira' appearing in name field",
    #     )
    #     self.assertEqual(
    #         len(response.json()["hashtags"]),
    #         1,
    #         msg="Filtered result should contain 1 hashTag with the string 'jira' appearing in value field",
    #     )
    #     self.assertEqual(
    #         len(response.json()["groups"]),
    #         0,
    #         msg="Filtered result should contain 0 groups with the string 'jira' appearing in value field",
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?freeSearch={}".format("park"),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["hashtags"]),
    #         1,
    #         msg="Filtered result should contain 1 hashTag with the string 'park' appearing in value field",
    #     )
    #     self.assertEqual(
    #         len(response.json()["projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project with the string 'park' appearing in name field",
    #     )
    #     self.assertEqual(
    #         len(response.json()["groups"]),
    #         1,
    #         msg="Filtered result should contain 1 group with the string 'park' appearing in name field",
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?freeSearch={}".format("Parking"),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project with the string 'Parking' appearing in name field",
    #     )
    #     self.assertEqual(
    #         len(response.json()["hashtags"]),
    #         0,
    #         msg="Filtered result should contain no hashtags with the string 'Parking' appearing in value field",
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?programmed={}".format("false"),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         2,
    #         msg="Filtered result should conresults with field programmed = false. Found: {}".format(
    #             len(response.json()["results"])
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?programmed={}&programmed={}".format(
    #             "false", "true"
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         Project.objects.all().count(),
    #         msg="Filtered result should contain all projects existing in the DB",
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?programmed={}&hkrId={}".format("false", "3333"),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         1,
    #         msg="Filtered result should contain 1 project with field programmed = false and hkrId = 333. Found: {}".format(
    #             len(response.json()["results"])
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?masterClass={}".format(
    #             self.projectMasterClass_2_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         4,
    #         msg="Filtered result should contain 4 projects belonging to masterClass Id: {}, directly or indirectly. Found: {}".format(
    #             self.projectMasterClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         3,
    #         msg="Filtered result should contain 3 classes with projects linked to it. Found: {}".format(
    #             len([x for x in response.json()["results"] if x["type"] == "classes"])
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?subClass={}&masterClass={}".format(
    #             self.projectSubClass_2_Id, self.projectMasterClass_3_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         0,
    #         msg="Filtered result should contain 0 projects with masterClass Id: {} and subClass Id: {}. Found: {}".format(
    #             self.projectMasterClass_3_Id,
    #             self.projectSubClass_2_Id,
    #             len(response.json()["results"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len(response.json()["results"]),
    #         0,
    #         msg="Filtered result should contain 0 classes",
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?subClass={}".format(self.projectSubClass_1_Id),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project belonging to subClass Id: {}. Found: {}".format(
    #             self.projectSubClass_1_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         1,
    #         msg="Filtered result should contain 1 class with id {}. Found: {}".format(
    #             self.projectSubClass_1_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?subClass={}&subClass={}".format(
    #             self.projectSubClass_1_Id, self.projectSubClass_2_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         2,
    #         msg="Filtered result should contain a project belonging to subClass Id: {} and another belonging to subClass Id: {}. Found: {}".format(
    #             self.projectSubClass_1_Id,
    #             self.projectSubClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         2,
    #         msg="Filtered result should contain 2 classes with id {} and {}. Found: {}".format(
    #             self.projectSubClass_1_Id,
    #             self.projectSubClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?subClass={}&category={}".format(
    #             self.projectSubClass_2_Id, self.projectCategory_3_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         1,
    #         msg="Filtered result should contain a project belonging to subClass Id: {} and category Id: {}. Found: {}".format(
    #             self.projectSubClass_2_Id,
    #             self.projectCategory_3_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         1,
    #         msg="Filtered result should contain 1 class with id {}. Found: {}".format(
    #             self.projectSubClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?class={}".format(self.projectClass_2_Id),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         4,
    #         msg="Filtered result should contain 4 projects belonging to class Id: {}, directly or indirectly. Found: {}".format(
    #             self.projectClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?class={}&direct=true".format(
    #             self.projectClass_2_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project belonging to class Id: {}, directly. Found: {}".format(
    #             self.projectClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         1,
    #         msg="Filtered result should contain 1 class with id {}. Found: {}".format(
    #             self.projectClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?district={}".format(self.projectDistrict_2_Id),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         3,
    #         msg="Filtered result should contain 3 projects belonging to district Id: {}, directly or indirectly. Found: {}".format(
    #             self.projectDistrict_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "locations"]),
    #         3,
    #         msg="Filtered result should contain 3 locations with id {}, {} and {}. Found: {}".format(
    #             self.projectDistrict_2_Id,
    #             self.projectSubDivision_1_Id,
    #             self.projectSubDivision_2_Id,
    #             len(
    #                 [x for x in response.json()["results"] if x["type"] == "locations"]
    #             ),
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?district={}&direct=true".format(
    #             self.projectDistrict_2_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project belonging to district Id: {} directly. Found: {}".format(
    #             self.projectDistrict_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "locations"]),
    #         1,
    #         msg="Filtered result should contain 1 locations with id {}. Found: {}".format(
    #             self.projectDistrict_2_Id,
    #             len(
    #                 [x for x in response.json()["results"] if x["type"] == "locations"]
    #             ),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?district={}&hashtag={}".format(
    #             self.projectDistrict_3_Id, self.projectHashTag_3_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project belonging to district Id: {}, directly or indirectly, \
    #             with the hashTag: {} . Found: {}".format(
    #             self.projectDistrict_3_Id,
    #             self.projectHashTag_3_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "locations"]),
    #         1,
    #         msg="Filtered result should contain 1 locations with id {}. Found: {}".format(
    #             self.projectDistrict_2_Id,
    #             len(
    #                 [x for x in response.json()["results"] if x["type"] == "locations"]
    #             ),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?district={}&district={}".format(
    #             self.projectDistrict_2_Id, self.projectDistrict_3_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         4,
    #         msg="Filtered result should contain 4 projects belonging to district Id: {} or {}, directly or indirectly. Found: {}".format(
    #             self.projectDistrict_2_Id,
    #             self.projectDistrict_3_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "locations"]),
    #         4,
    #         msg="Filtered result should contain 4 locations with id {}, {}, {} and {}. Found: {}".format(
    #             self.projectDistrict_2_Id,
    #             self.projectDistrict_3_Id,
    #             self.projectSubDivision_1_Id,
    #             self.projectSubClass_2_Id,
    #             len(
    #                 [x for x in response.json()["results"] if x["type"] == "locations"]
    #             ),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?district={}&programmed={}".format(
    #             self.projectDistrict_3_Id, "false"
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project belonging to district Id: {}, directly or indirectly, and field programmed = false. Found: {}".format(
    #             self.projectDistrict_3_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "locations"]),
    #         1,
    #         msg="Filtered result should contain 1 location with id {}. Found: {}".format(
    #             self.projectDistrict_3_Id,
    #             len(
    #                 [x for x in response.json()["results"] if x["type"] == "locations"]
    #             ),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?masterClass={}&subClass={}".format(
    #             self.projectMasterClass_2_Id, self.projectSubClass_2_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project belonging to masterClass Id: {}, directly or indirectly, and field programmed = false. Found: {}".format(
    #             self.projectMasterClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         1,
    #         msg="Filtered result should contain 1 class with id {}. Found: {}".format(
    #             self.projectSubClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?programmed={}&category={}".format(
    #             "true", self.projectCategory_3_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         2,
    #         msg="Filtered result should contain 2 project with field programmed = true and category Id: {}. Found: {}".format(
    #             self.projectCategory_3_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?masterClass={}&masterClass={}&subClass={}&subClass={}".format(
    #             self.projectMasterClass_2_Id,
    #             self.projectMasterClass_3_Id,
    #             self.projectSubClass_1_Id,
    #             self.projectSubClass_2_Id,
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         2,
    #         msg="Filtered result should contain 2 projects belonging to masterClass Id: {}, directly or indirectly, and subClass Id: {} or {} each. Found: {}".format(
    #             self.projectMasterClass_2_Id,
    #             self.projectSubClass_1_Id,
    #             self.projectSubClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         2,
    #         msg="Filtered result should contain 2 classes with id {} and {}. Found: {}".format(
    #             self.projectSubClass_1_Id,
    #             self.projectSubClass_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?hashtag={}".format(self.projectHashTag_3_Id),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )

    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         2,
    #         msg="Filtered result should contain 2 projects with hashTag: {}. Found: {}".format(
    #             self.projectHashTag_3_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?hashtag={}&hashtag={}".format(
    #             self.projectHashTag_3_Id, self.projectHashTag_4_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         3,
    #         msg="Filtered result should contain 3 projects with hashTag: {} or {}. Found: {}".format(
    #             self.projectHashTag_3_Id,
    #             self.projectHashTag_4_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?hashtag={}&hashtag={}&group={}".format(
    #             self.projectHashTag_3_Id,
    #             self.projectHashTag_4_Id,
    #             self.projectGroup_1_Id,
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )

    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         2,
    #         msg="Filtered result should contain 2 projects with hashTag: {} or {} and group: {}. Found: {}".format(
    #             self.projectHashTag_3_Id,
    #             self.projectHashTag_4_Id,
    #             self.projectGroup_1_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "groups"]),
    #         1,
    #         msg="Filtered result should contain 1 group with id {}. Found: {}".format(
    #             self.projectGroup_1_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "groups"]),
    #         ),
    #     )
    #     response = self.client.get(
    #         "/projects/search-results/?group={}&group={}".format(
    #             self.projectGroup_2_Id,
    #             self.projectGroup_1_Id,
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )

    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         4,
    #         msg="Filtered result should contain 4 projects with groups: {} or {}. Found: {}".format(
    #             self.projectGroup_2_Id,
    #             self.projectGroup_1_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "groups"]),
    #         2,
    #         msg="Filtered result should contain 2 groups with id {} and {}. Found: {}".format(
    #             self.projectGroup_1_Id,
    #             self.projectGroup_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "groups"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         [x for x in response.json()["results"] if x["type"] == "groups"][0][
    #             "programmed"
    #         ],
    #         None,
    #         msg="Groups in search result should have programmed field set to None",
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?group={}&group={}&subClass={}&district={}".format(
    #             self.projectGroup_2_Id,
    #             self.projectGroup_1_Id,
    #             self.projectSubClass_1_Id,
    #             self.projectDistrict_2_Id,
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )

    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project with group {} or {}, subClass {} and district {}. Found: {}".format(
    #             self.projectGroup_1_Id,
    #             self.projectGroup_2_Id,
    #             self.projectSubClass_1_Id,
    #             self.projectDistrict_2_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         1,
    #         msg="Filtered result should contain 1 class with id {}. Found: {}".format(
    #             self.projectSubClass_1_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "classes"]),
    #         ),
    #     )
    #     self.assertEqual(
    #         [x for x in response.json()["results"] if x["type"] == "classes"][0][
    #             "programmed"
    #         ],
    #         None,
    #         msg="Classes in search result should have programmed field set to None",
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "locations"]),
    #         1,
    #         msg="Filtered result should contain 1 location with id {}. Found: {}".format(
    #             self.projectDistrict_2_Id,
    #             len(
    #                 [x for x in response.json()["results"] if x["type"] == "locations"]
    #             ),
    #         ),
    #     )
    #     self.assertEqual(
    #         [x for x in response.json()["results"] if x["type"] == "locations"][0][
    #             "programmed"
    #         ],
    #         None,
    #         msg="Locations in search result should have programmed field set to None",
    #     )
    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "groups"]),
    #         1,
    #         msg="Filtered result should contain 1 group with id {}. Found: {}".format(
    #             self.projectGroup_1_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "groups"]),
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?personPlanning={}".format(self.person_4_Id),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )

    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         4,
    #         msg="Filtered result should contain 4 projects with personPlanning {}. Found: {}".format(
    #             self.person_4_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?project={}&project={}".format(
    #             self.project_3_Id, self.project_4_Id
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )

    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         2,
    #         msg="Filtered result should contain 2 projects with id {} and {}".format(
    #             self.project_3_Id, self.project_4_Id
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?project={}&project={}&projectName={}".format(
    #             self.project_3_Id, self.project_4_Id, "park"
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )

    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project with id {} and the string 'park' in its name. Found: {}".format(
    #             self.project_3_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?inGroup={}".format("false"),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )

    #     self.assertEqual(
    #         len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         1,
    #         msg="Filtered result should contain 1 project with id: {}. Found: {}".format(
    #             self.project_1_Id,
    #             len([x for x in response.json()["results"] if x["type"] == "projects"]),
    #         ),
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?project={}".format(self.project_5_Id),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         response.json()["results"][0]["path"],
    #         "{}/{}/{}/{}".format(
    #             self.projectMasterClass_2_Id,
    #             self.projectClass_2_Id,
    #             self.projectSubClass_2_Id,
    #             self.projectDistrict_3_Id,
    #         ),
    #         msg="Path does not follow the format masterClass/class/subClass/district",
    #     )

    #     response = self.client.get(
    #         "/projects/search-results/?project={}".format(
    #             self.project_3_Id,
    #         ),
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )

    #     self.assertEqual(
    #         response.json()["count"],
    #         1,
    #         msg="Should return 1 project with id: {}".format(self.project_3_Id),
    #     )
    #     self.assertEqual(
    #         response.json()["results"][0]["programmed"],
    #         True,
    #         msg="programmed field in response should be `True`",
    #     )

    # # Commented out test to check if a project gets locked automatically on phase change
    # # def test_project_gets_locked_on_phase_change(self):
    # #     ProjectPhase.objects.create(id=self.projectPhase_2_Id, value="construction")
    # #     data = {
    # #         "name": "Test locking",
    # #         "description": "Test Description",
    # #         "phase": self.projectPhase_2_Id.__str__(),
    # #     }
    # #     response = self.client.post(
    # #         "/projects/",
    # #         data,
    # #         content_type="application/json",
    # #     )
    # #     newCreatedId = response.json()["id"]
    # #     self.assertEqual(
    # #         response.status_code,
    # #         201,
    # #         msg="Status code != 201 , Error: {}".format(response.json()),
    # #     )
    # #     self.assertTrue(
    # #         ProjectLock.objects.filter(project=newCreatedId).exists(),
    # #         msg="ProjectLock does not contain a record for new created project with id {} when phase is set to construction".format(
    # #             newCreatedId
    # #         ),
    # #     )

    # #     data["phase"] = self.projectPhase_1_Id.__str__()
    # #     response = self.client.post(
    # #         "/projects/",
    # #         data,
    # #         content_type="application/json",
    # #     )
    # #     newCreatedId = response.json()["id"]
    # #     self.assertEqual(
    # #         response.status_code,
    # #         201,
    # #         msg="Status code != 200 , Error: {}".format(response.json()),
    # #     )
    # #     self.assertFalse(
    # #         ProjectLock.objects.filter(project=newCreatedId).exists(),
    # #         msg="ProjectLock contains a record for new created project with id {} when phase is not set to construction".format(
    # #             newCreatedId
    # #         ),
    # #     )

    # #     data["phase"] = self.projectPhase_2_Id.__str__()
    # #     response = self.client.patch(
    # #         "/projects/{}/".format(newCreatedId),
    # #         data,
    # #         content_type="application/json",
    # #     )
    # #     self.assertEqual(
    # #         response.status_code,
    # #         200,
    # #         msg="Status code != 200 , Error: {}".format(response.json()),
    # #     )
    # #     self.assertTrue(
    # #         ProjectLock.objects.filter(project=newCreatedId).exists(),
    # #         msg="ProjectLock does not contain a record for updated project with id {} when phase is updated to construction".format(
    # #             newCreatedId
    # #         ),
    # #     )

    # def test_project_gets_locked(self):
    #     Project.objects.create(
    #         id=self.project_7_Id,
    #         name="Test project fields lock",
    #         description="Test description",
    #         constructionEndYear=2027,
    #         planningStartYear=2020,
    #     )
    #     Person.objects.create(
    #         id=self.person_7_Id,
    #         firstName="John",
    #         lastName="Doe",
    #         email="random@random.com",
    #         title="Manager",
    #         phone="0414853275",
    #     )
    #     data = {
    #         "project": self.project_7_Id.__str__(),
    #         "lockedBy": self.person_7_Id.__str__(),
    #         "lockType": "byPerson",
    #     }
    #     response = self.client.post(
    #         "/project-locks/",
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(
    #         response.status_code,
    #         201,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {"phase": self.projectPhase_1_Id.__str__()}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field phase cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"planningStartYear": 2023}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field planningStartYear cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"constructionEndYear": 2023}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field constructionEndYear cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"programmed": False}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field programmed cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"projectClass": self.projectClass_1_Id.__str__()}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field projectClass cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"projectLocation": self.projectDivision_1_Id.__str__()}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field projectLocation cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"siteId": self.budgetItemId.__str__()}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field siteId cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"realizedCost": 200}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field realizedCost cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"budgetOverrunAmount": 200}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field budgetOverrunAmount cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"budgetForecast1CurrentYear": 200}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field budgetForecast1CurrentYear cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"budgetForecast2CurrentYear": 200}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field budgetForecast2CurrentYear cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"budgetForecast3CurrentYear": 200}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field budgetForecast3CurrentYear cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"budgetForecast4CurrentYear": 200}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field budgetForecast4CurrentYear cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"budgetProposalCurrentYearPlus0": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field budgetProposalCurrentYearPlus0 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"budgetProposalCurrentYearPlus1": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field budgetProposalCurrentYearPlus1 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"budgetProposalCurrentYearPlus2": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field budgetProposalCurrentYearPlus2 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"preliminaryCurrentYearPlus3": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field preliminaryCurrentYearPlus3 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"preliminaryCurrentYearPlus4": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field preliminaryCurrentYearPlus4 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"preliminaryCurrentYearPlus5": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field preliminaryCurrentYearPlus5 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"preliminaryCurrentYearPlus6": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field preliminaryCurrentYearPlus6 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"preliminaryCurrentYearPlus7": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field preliminaryCurrentYearPlus7 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"preliminaryCurrentYearPlus8": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field preliminaryCurrentYearPlus8 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"preliminaryCurrentYearPlus9": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field preliminaryCurrentYearPlus9 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"finances": {"preliminaryCurrentYearPlus10": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_7_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "The field preliminaryCurrentYearPlus10 cannot be modified when the project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    # def test_locking_project_twice(self):
    #     Project.objects.create(
    #         id=self.project_8_Id,
    #         name="Test locking twice",
    #         description="Test description",
    #     )
    #     Person.objects.create(
    #         id=self.person_5_Id,
    #         firstName="John",
    #         lastName="Doe",
    #         email="random@random.com",
    #         title="Manager",
    #         phone="0414853275",
    #     )
    #     data = {
    #         "project": self.project_8_Id.__str__(),
    #         "lockedBy": self.person_5_Id.__str__(),
    #         "lockType": "byPerson",
    #     }
    #     response = self.client.post(
    #         "/project-locks/",
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(
    #         response.status_code,
    #         201,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {
    #         "project": self.project_8_Id.__str__(),
    #         "lockedBy": self.person_5_Id.__str__(),
    #         "lockType": "byPerson",
    #     }
    #     response = self.client.post(
    #         "/project-locks/",
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )

    # def test_date_validation_on_lock(self):
    #     Project.objects.create(
    #         id=self.project_8_Id,
    #         name="Test project fields lock",
    #         description="Test description",
    #         planningStartYear=2023,
    #         constructionEndYear=2025,
    #     )
    #     Person.objects.create(
    #         id=self.person_6_Id,
    #         firstName="John",
    #         lastName="Doe",
    #         email="random@random.com",
    #         title="Manager",
    #         phone="0414853275",
    #     )
    #     data = {
    #         "project": self.project_8_Id.__str__(),
    #         "lockedBy": self.person_6_Id.__str__(),
    #         "lockType": "byPerson",
    #     }
    #     response = self.client.post(
    #         "/project-locks/",
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(
    #         response.status_code,
    #         201,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {"estPlanningStart": "05.05.2020"}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_8_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "estPlanningStart date cannot be set to a earlier date than Start year of planning when project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"estConstructionEnd": "05.05.2030"}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_8_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "estConstructionEnd date cannot be set to a later date than End year of construction when project is locked",
    #         response.json()["errors"][0]["detail"],
    #     )

    # def test_class_location_validation(self):
    #     district_1 = ProjectLocation.objects.create(
    #         id=self.projectDistrict_4_Id,
    #         name="Eteläinen",
    #         parent=None,
    #         path="Eteläinen",
    #     )
    #     district_2 = ProjectLocation.objects.create(
    #         id=self.projectDistrict_5_Id,
    #         name="Läntinen",
    #         parent=None,
    #         path="Läntinen",
    #     )
    #     district_3 = ProjectLocation.objects.create(
    #         id=self.projectDistrict_6_Id,
    #         name="Keskinen",
    #         parent=None,
    #         path="Keskinen",
    #     )
    #     district_4 = ProjectLocation.objects.create(
    #         id=self.projectDistrict_7_Id,
    #         name="Östersundom",
    #         parent=None,
    #         path="Östersundom",
    #     )
    #     district_1.childLocation.create(
    #         id=self.projectDivision_3_Id,
    #         name="Munkkiniemi",
    #         path="Eteläinen/Munkkiniemi",
    #     )
    #     district_2.childLocation.create(
    #         id=self.projectDivision_4_Id,
    #         name="Munkkiniemi",
    #         path="Läntinen/Munkkiniemi",
    #     )
    #     district_3.childLocation.create(
    #         id=self.projectDivision_5_Id,
    #         name="Munkkiniemi",
    #         path="Keskinen/Munkkiniemi",
    #     )
    #     district_4.childLocation.create(
    #         id=self.projectDivision_6_Id,
    #         name="ostersundomTest",
    #         path="Östersundom/ostersundomTest",
    #     )

    #     masterClass_1 = ProjectClass.objects.create(
    #         id=self.projectMasterClass_3_Id,
    #         name="803 Kadut, liikenneväylät",
    #         parent=None,
    #         path="803 Kadut, liikenneväylät",
    #     )
    #     _class = masterClass_1.childClass.create(
    #         name="Uudisrakentaminen",
    #         id=self.projectClass_3_Id,
    #         path="803 Kadut, liikenneväylät/Uudisrakentaminen",
    #     )
    #     _class.childClass.create(
    #         name="Läntinen suurpiiri",
    #         id=self.projectSubClass_3_Id,
    #         path="803 Kadut, liikenneväylät/Uudisrakentaminen/Läntinen suurpiiri",
    #     )
    #     _class.childClass.create(
    #         name="Eteläinen suurpiiri",
    #         id=self.projectSubClass_4_Id,
    #         path="803 Kadut, liikenneväylät/Uudisrakentaminen/Eteläinen suurpiiri",
    #     )
    #     _class.childClass.create(
    #         name="Östersundomin suurpiiri",
    #         id=self.projectSubClass_5_Id,
    #         path="803 Kadut, liikenneväylät/Uudisrakentaminen/Östersundomin suurpiiri",
    #     )
    #     _class.childClass.create(
    #         name="Siltojen peruskorjaus ja uusiminen",
    #         id=self.projectSubClass_6_Id,
    #         path="803 Kadut, liikenneväylät/Uudisrakentaminen/Siltojen peruskorjaus ja uusiminen",
    #     )

    #     data = {
    #         "name": "Class Location Validation project",
    #         "description": "Test Description",
    #         "projectClass": self.projectSubClass_4_Id.__str__(),
    #         "projectLocation": self.projectDivision_3_Id.__str__(),
    #     }

    #     # Creating project with Class "Eteläinen suurpiiri" and location path "Eteläinen/Munkkiniemi"
    #     # Current class is "Läntinen suurpiiri"
    #     # Current location path is "Eteläinen/Munkkiniemi"
    #     response = self.client.post(
    #         "/projects/",
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         201,
    #         msg="Status code != 201 , Error: {}".format(response.json()),
    #     )

    #     newProjectId = response.json()["id"]

    #     data = {
    #         "projectLocation": self.projectDivision_4_Id.__str__(),
    #     }

    #     # Patching project with location path "Läntinen/Munkkiniemi"
    #     # Current class is "Eteläinen suurpiiri"
    #     # Current location path is "Läntinen/Munkkiniemi"
    #     response = self.client.patch(
    #         "/projects/{}/".format(newProjectId),
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(response.status_code, 400, msg=response.json())

    #     data = {
    #         "projectClass": self.projectSubClass_3_Id.__str__(),
    #         "projectLocation": self.projectDivision_4_Id.__str__(),
    #     }

    #     # Patching project with location path "Läntinen/Munkkiniemi" and class "Läntinen suurpiiri"
    #     # Current class is "Läntinen suurpiiri"
    #     # Current location path is "Läntinen/Munkkiniemi"
    #     response = self.client.patch(
    #         "/projects/{}/".format(newProjectId),
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(response.status_code, 200, msg=response.json())

    #     data = {
    #         "projectClass": self.projectSubClass_5_Id.__str__(),
    #         "projectLocation": self.projectDivision_6_Id.__str__(),
    #     }

    #     # Patching project with location path "Östersundom/ostersundomTest" and class "Östersundomin suurpiiri"
    #     # Current class is "Östersundomin suurpiiri"
    #     # Current location path is "Östersundom/ostersundomTest"
    #     response = self.client.patch(
    #         "/projects/{}/".format(newProjectId),
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(response.status_code, 200, msg=response.json())

    #     data = {
    #         "projectLocation": self.projectDivision_3_Id.__str__(),
    #     }

    #     # Patching project with location path "Eteläinen/Munkkiniemi"
    #     # Current class is "Östersundomin suurpiiri"
    #     # Current location path is "Eteläinen/Munkkiniemi"
    #     response = self.client.patch(
    #         "/projects/{}/".format(newProjectId),
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(response.status_code, 400, msg=response.json())

    #     data = {
    #         "projectClass": self.projectSubClass_6_Id.__str__(),
    #     }

    #     # Patching project with class "Siltojen peruskorjaus ja uusiminen"
    #     # Current class is "Siltojen peruskorjaus ja uusiminen"
    #     # Current location path is "Eteläinen/Munkkiniemi"
    #     response = self.client.patch(
    #         "/projects/{}/".format(newProjectId),
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(response.status_code, 200, msg=response.json())

    #     data = {
    #         "projectLocation": self.projectDivision_5_Id.__str__(),
    #     }

    #     # Patching project with location path "Keskinen/Munkkiniemi"
    #     # Current class is "Siltojen peruskorjaus ja uusiminen"
    #     # Current location path is "Keskinen/Munkkiniemi"
    #     response = self.client.patch(
    #         "/projects/{}/".format(newProjectId),
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(response.status_code, 200, msg=response.json())

    #     data = {
    #         "projectClass": self.projectSubClass_3_Id.__str__(),
    #     }

    #     # Patching project with class "Läntinen suurpiiri"
    #     # Current class is "Läntinen suurpiiri"
    #     # Current location path is "Keskinen/Munkkiniemi"
    #     response = self.client.patch(
    #         "/projects/{}/".format(newProjectId),
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(response.status_code, 400, msg=response.json())

    # def test_project_finances(self):
    #     response = self.client.get(
    #         "/projects/{}/".format(self.project_1_Id),
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         response.json()["finances"]["year"],
    #         date.today().year,
    #         msg="Project does not contain current year finances by default",
    #     )

    #     response = self.client.get(
    #         "/projects/{}/".format(2025),
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         response.json()["results"][0]["finances"]["year"],
    #         2025,
    #         msg="Projects does not contain finances from the URL query year",
    #     )
    #     data = {"finances": {"year": 2050, "budgetProposalCurrentYearPlus0": 200}}
    #     response = self.client.patch(
    #         "/projects/{}/".format(self.project_1_Id),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         response.json()["finances"]["year"],
    #         2050,
    #         msg="Finances year != 2050",
    #     )
    #     self.assertEqual(
    #         response.json()["finances"]["budgetProposalCurrentYearPlus0"],
    #         "200.00",
    #         msg="budgetProposalCurrentYearPlus0 != 200.00",
    #     )
    #     response = self.client.get(
    #         "/projects/{}/".format(2050),
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200, Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         response.json()["results"][0]["finances"]["year"],
    #         2050,
    #         msg="Projects does not contain finances from the URL query year",
    #     )
    #     self.assertEqual(
    #         response.json()["results"][0]["finances"]["budgetProposalCurrentYearPlus0"],
    #         "200.00",
    #         msg="budgetProposalCurrentYearPlus0 != 200.00",
    #     )

    # def test_other_field_validations(self):
    #     self.projectPhase_2_Id = ProjectPhase.objects.get(
    #         value="programming"
    #     ).id.__str__()
    #     self.projectPhase_3_Id = ProjectPhase.objects.get(
    #         value="completed"
    #     ).id.__str__()
    #     self.projectPhase_4_Id = ProjectPhase.objects.get(
    #         value="draftInitiation"
    #     ).id.__str__()
    #     self.projectPhase_5_Id = ProjectPhase.objects.get(
    #         value="construction"
    #     ).id.__str__()
    #     self.projectPhase_6_Id = ProjectPhase.objects.get(
    #         value="warrantyPeriod"
    #     ).id.__str__()
    #     ConstructionPhaseDetail.objects.create(
    #         id=self.conPhaseDetail_2_Id, value="preConstruction"
    #     )
    #     data = {
    #         "name": "Testing fields",
    #         "description": "Test Desc",
    #         "programmed": True,
    #     }
    #     response = self.client.post(
    #         "/projects/",
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "category must be populated if programmed is `True`",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {
    #         "name": "Testing fields",
    #         "description": "Test Desc",
    #         "programmed": False,
    #     }
    #     response = self.client.post(
    #         "/projects/",
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "phase must be set to `proposal` or `design` if programmed is `False`",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {
    #         "name": "Testing fields",
    #         "description": "Test Desc",
    #     }
    #     response = self.client.post(
    #         "/projects/",
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         201,
    #         msg="Status code != 201 , Error: {}".format(response.json()),
    #     )
    #     createdId = response.json()["id"]

    #     data = {"phase": self.projectPhase_2_Id}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "planningStartYear and constructionEndYear must be populated if phase is `programming`",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {
    #         "phase": self.projectPhase_2_Id,
    #         "planningStartYear": 2015,
    #         "constructionEndYear": 2020,
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "category must be populated if phase is `programming`",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {
    #         "phase": self.projectPhase_4_Id,
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "estPlanningStart and estPlanningEnd must be populated if phase is `draftInitiation`",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {
    #         "phase": self.projectPhase_4_Id,
    #         "estPlanningStart": "01.01.2023",
    #         "estPlanningEnd": "01.01.2024",
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "personPlanning must be populated if phase is `draftInitiation`",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {
    #         "estPlanningStart": "01.01.2023",
    #         "estPlanningEnd": "01.01.2024",
    #         "personPlanning": self.person_1_Id,
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )
    #     data = {
    #         "phase": self.projectPhase_4_Id,
    #         "programmed": True,
    #         "category": self.projectCategory_1_Id,
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {
    #         "phase": self.projectPhase_5_Id,
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "estConstructionStart and estConstructionEnd must be populated if phase is `construction`",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {
    #         "phase": self.projectPhase_5_Id,
    #         "estConstructionStart": "01.01.2023",
    #         "estConstructionEnd": "01.01.2024",
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "personConstruction must be populated if phase is `construction`",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {
    #         "estConstructionStart": "01.01.2023",
    #         "estConstructionEnd": "01.01.2024",
    #         "personConstruction": self.person_2_Id,
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {"phase": self.projectPhase_5_Id}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {"phase": self.projectPhase_6_Id}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "phase cannot be `warrantyPeriod` if current date is earlier than estConstructionEnd",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {
    #         "constructionPhaseDetail": self.conPhaseDetail_2_Id,
    #         "phase": self.projectPhase_2_Id,
    #         "planningStartYear": 2021,
    #         "constructionEndYear": 2022,
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "constructionPhase detail cannot be populated if phase is not `construction`",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {
    #         "constructionPhaseDetail": self.conPhaseDetail_2_Id,
    #         "phase": self.projectPhase_5_Id,
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {"programmed": False}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "phase must be set to `proposal` or `design` if programmed is `False`",
    #         response.json()["errors"][0]["detail"],
    #     )
    #     # Getting proposal phase from the data that is populated when tests run the migrations
    #     data = {
    #         "programmed": False,
    #         "phase": ProjectPhase.objects.get(value="proposal").id,
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {"programmed": True}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "phase cannot be `proposal` or `design` if programmed is `True`",
    #         response.json()["errors"][0]["detail"],
    #     )
    #     data = {"programmed": True, "phase": self.projectPhase_2_Id,"planningStartYear":2021,"constructionEndYear":2022}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {"planningStartYear": 2050}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "Year cannot be later than constructionEndYear",
    #         response.json()["errors"][0]["detail"],
    #     )
    #     data = {"planningStartYear": 2050, "constructionEndYear": 2060}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )
    #     data = {"constructionEndYear": 2030}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "Year cannot be earlier than planningStartYear",
    #         response.json()["errors"][0]["detail"],
    #     )

    #     data = {"constructionEndYear": 2055}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {"estPlanningStart": "01.01.2023", "estPlanningEnd": "01.01.2020"}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "Date cannot be later than estPlanningEnd",
    #         response.json()["errors"][0]["detail"],
    #     )
    #     data = {"estPlanningStart": "01.01.2023", "estPlanningEnd": "01.01.2025"}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {"presenceStart": "01.01.2023", "presenceEnd": "01.01.2020"}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "Date cannot be later than presenceEnd",
    #         response.json()["errors"][0]["detail"],
    #     )
    #     data = {"presenceStart": "01.01.2023", "presenceEnd": "01.01.2025"}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {"visibilityStart": "01.01.2023", "visibilityEnd": "01.01.2020"}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "Date cannot be later than visibilityEnd",
    #         response.json()["errors"][0]["detail"],
    #     )
    #     data = {"visibilityStart": "01.01.2023", "visibilityEnd": "01.01.2025"}
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    #     data = {
    #         "estConstructionStart": "01.01.2023",
    #         "estConstructionEnd": "01.01.2020",
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         400,
    #         msg="Status code != 400 , Error: {}".format(response.json()),
    #     )
    #     self.assertEqual(
    #         "Date cannot be later than estConstructionEnd",
    #         response.json()["errors"][0]["detail"],
    #     )
    #     data = {
    #         "estConstructionStart": "01.01.2023",
    #         "estConstructionEnd": "01.01.2025",
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(createdId),
    #         data,
    #         content_type="application/json",
    #     )
    #     self.assertEqual(
    #         response.status_code,
    #         200,
    #         msg="Status code != 200 , Error: {}".format(response.json()),
    #     )

    # def test_pw_folder_project(self):
    #     data = {
    #         "name": "Test Project for PW folder",
    #         "description": "Test description",
    #         "hkrId": self.pwInstanceId_hkrId_1,
    #     }
    #     response = self.client.post(
    #         "/projects/",
    #         data,
    #         content_type="application/json",
    #     )
    #     newCreatedId = response.json()["id"]
    #     self.assertEqual(response.status_code, 201)

    #     response = self.client.get(
    #         "/projects/{}/".format(newCreatedId),
    #         content_type="application/json",
    #     )

    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(
    #         response.json()["pwFolderLink"], self.pwInstanceId_hkrId_1_folder
    #     )

    #     data = {
    #         "hkrId": self.pwInstanceId_hkrId_2,
    #     }
    #     response = self.client.patch(
    #         "/projects/{}/".format(newCreatedId),
    #         data,
    #         content_type="application/json",
    #     )

    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(
    #         response.json()["pwFolderLink"], self.pwInstanceId_hkrId_2_folder
    #     )
