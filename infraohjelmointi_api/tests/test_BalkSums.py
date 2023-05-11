from django.test import TestCase
from rest_framework.renderers import JSONRenderer
from infraohjelmointi_api.models import (
    Project,
    ProjectClass,
    ProjectFinancial,
    ProjectGroup,
    ProjectLocation,
)

import uuid
from overrides import override


class BalkSumTestCase(TestCase):
    project_1_Id = uuid.UUID("d6e03aa6-1ffa-4603-86ff-0d22dccf702d")
    project_2_Id = uuid.UUID("d27bbbcc-22de-48c6-b96a-899d8cf3e3da")
    project_3_Id = uuid.UUID("fee7ce1c-ac73-474f-95d6-3b021c7c267d")
    project_4_Id = uuid.UUID("54f04351-35bf-45af-b555-093781f18941")
    project_5_Id = uuid.UUID("2520268e-617a-4dd2-ad66-74c76a70de83")
    project_6_Id = uuid.UUID("7f95f757-d8a7-4976-93c5-4acea075eee4")
    project_7_Id = uuid.UUID("899ee2a2-37f4-490f-976c-949551fab177")
    project_8_Id = uuid.UUID("0e9c3042-32cf-4faa-b1e9-dab7304b8202")
    project_9_Id = uuid.UUID("1fbe6038-b9d6-4832-8403-ec95c9a5749a")
    project_10_Id = uuid.UUID("2546b016-fd8c-45c3-b43e-0a1db86a04b5")
    projectClass_1_Id = uuid.UUID("0f452428-d6b6-461e-b93c-fdd9a1b93bb4")
    projectClass_2_Id = uuid.UUID("a4b3f506-c3b3-4d4d-a34e-ab0903ed926c")
    projectClass_3_Id = uuid.UUID("369f31e0-7f4c-4761-b30b-13b604d8b94e")
    projectSubClass_1_Id = uuid.UUID("e799731e-a9a1-4472-a480-bf6c5cad6b30")
    projectSubClass_2_Id = uuid.UUID("519a89ae-1060-4771-802d-decc7ef0f843")
    projectSubClass_3_Id = uuid.UUID("24bc3bd5-ca10-4005-b573-89fca9657ed2")
    projectSubClass_4_Id = uuid.UUID("1c74f82e-dc46-4fd4-b8de-71a6a3c3e085")
    projectSubClass_5_Id = uuid.UUID("a67dbfc5-7e4f-44e0-b0bd-219f46a1f9ce")
    projectSubClass_6_Id = uuid.UUID("de3812f3-a9fd-485f-93e9-3af3b929bb71")
    projectMasterClass_1_Id = uuid.UUID("fcd31639-2d17-4d5e-a602-2f5983d8f06a")
    projectMasterClass_2_Id = uuid.UUID("8747ca1c-0318-4c35-af3b-d75d3068aea3")
    projectMasterClass_3_Id = uuid.UUID("79e0e266-6306-4ebd-ba91-1c38fc5e5903")
    projectMasterClass_4_Id = uuid.UUID("bfd4fb69-af94-43b4-add1-f7e6141e24db")
    projectDistrict_1_Id = uuid.UUID("ac47e81d-39e8-4d2b-b78a-8b1a74c4ebbc")
    projectDistrict_2_Id = uuid.UUID("ae2c7447-03bd-474e-b9c7-f348590ba687")
    projectDistrict_3_Id = uuid.UUID("85df171b-5d5f-4058-bf4e-4b39ab554bbc")
    projectDistrict_4_Id = uuid.UUID("bd66c000-461a-46c2-8b98-65edb5cf0b03")
    projectDistrict_5_Id = uuid.UUID("d7892ee4-dde6-4a68-9866-8bc5e0d44e00")
    projectDistrict_6_Id = uuid.UUID("5fac2254-6ca6-45ba-8b3e-c2ee206f94ee")
    projectDistrict_7_Id = uuid.UUID("4f056bca-58f4-4bb4-ac84-0f8a3c5221db")
    projectDivision_1_Id = uuid.UUID("1832b821-aca6-44f3-ac04-1f60cad89d49")
    projectDivision_2_Id = uuid.UUID("74379652-819d-411d-8544-cadf738cc416")
    projectDivision_3_Id = uuid.UUID("9cd08296-45d2-4847-9000-dc6d92681e23")
    projectDivision_4_Id = uuid.UUID("01b9bb89-1e35-4b83-bec3-5b57254efb5a")
    projectDivision_5_Id = uuid.UUID("e1d14e12-7e31-4d1e-8eaa-c27c4b424c53")
    projectDivision_6_Id = uuid.UUID("5a33e5d7-4792-4f2f-a30e-d76bae0a65bc")
    projectSubDivision_1_Id = uuid.UUID("27486130-ac05-4de4-a31e-2f6398f58359")
    projectSubDivision_2_Id = uuid.UUID("90ef4029-cc58-4187-98b4-3d8df9fd09e9")
    projectSubDivision_3_Id = uuid.UUID("67a52df2-e006-4fec-9040-384e6e72d1b6")
    projectGroup_1_Id = uuid.UUID("5740b0ae-d802-4785-bbc6-277a9853ecd8")
    projectGroup_2_Id = uuid.UUID("4b08bc44-3b94-44b4-8283-2b2ef07ed3fa")
    projectGroup_3_Id = uuid.UUID("661e8694-7840-43f2-b1c9-3dbed0c30cef")

    @classmethod
    @override
    def setUpTestData(self):
        projectGroup_1 = ProjectGroup.objects.create(
            id=self.projectGroup_1_Id, name="Test Group 1 rain"
        )
        projectGroup_2 = ProjectGroup.objects.create(
            id=self.projectGroup_2_Id, name="Test Group 2"
        )
        projectGroup_3 = ProjectGroup.objects.create(
            id=self.projectGroup_3_Id, name="Test Group 3 park"
        )
        district_1 = ProjectLocation.objects.create(
            id=self.projectDistrict_1_Id,
            name="District 1",
            parent=None,
            path="District 1",
        )
        district_2 = ProjectLocation.objects.create(
            id=self.projectDistrict_2_Id,
            name="District 2",
            parent=None,
            path="District 2",
        )
        division = district_1.childLocation.create(
            id=self.projectDivision_2_Id,
            name="District 1",
            path="District 1/Division 1",
        )
        subDivision_1 = division.childLocation.create(
            id=self.projectSubDivision_1_Id,
            name="SubDivision 1",
            path="District 1/Division 1/SubDivision 1",
        )
        subDivision_2 = division.childLocation.create(
            id=self.projectSubDivision_2_Id,
            name="SubDivision 2",
            path="District 1/Division 1/SubDivision 2",
        )

        masterClass_1 = ProjectClass.objects.create(
            id=self.projectMasterClass_1_Id,
            name="Master Class 1",
            parent=None,
            path="Master Class 1",
        )
        masterClass_2 = ProjectClass.objects.create(
            id=self.projectMasterClass_2_Id,
            name="Master Class 2",
            parent=None,
            path="Master Class 2",
        )
        _class = masterClass_1.childClass.create(
            name="Test Class 1",
            id=self.projectClass_1_Id,
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

        project_1 = Project.objects.create(
            id=self.project_1_Id,
            hkrId=2222,
            name="Parking Helsinki",
            description="Random desc",
            programmed=True,
            projectLocation=district_1,
            projectClass=subClass_1,
            projectGroup=projectGroup_1,
            costForecast=200,
        )

        project_2 = Project.objects.create(
            id=self.project_2_Id,
            hkrId=1111,
            name="Random name",
            description="Random desc",
            programmed=True,
            projectLocation=subDivision_1,
            projectClass=_class,
            projectGroup=projectGroup_1,
            costForecast=300,
        )

        project_3 = Project.objects.create(
            id=self.project_3_Id,
            hkrId=3333,
            name="Train Train Bike",
            description="Random desc",
            programmed=False,
            projectLocation=district_2,
            projectClass=subClass_2,
            projectGroup=projectGroup_2,
            costForecast=100,
        )

        project_4 = Project.objects.create(
            id=self.project_4_Id,
            hkrId=5555,
            name="Futurice Office Jira",
            description="Random desc",
            programmed=False,
            projectLocation=subDivision_2,
            projectClass=masterClass_2,
            projectGroup=projectGroup_3,
            costForecast=100,
        )
        project_5 = Project.objects.create(
            id=self.project_5_Id,
            hkrId=1111,
            name="Random name",
            description="Random desc",
            programmed=True,
            projectClass=_class,
            projectGroup=projectGroup_1,
            costForecast=100,
        )
        project_6 = Project.objects.create(
            id=self.project_6_Id,
            hkrId=1111,
            name="Random name",
            description="Random desc",
            programmed=True,
            projectClass=masterClass_1,
            costForecast=500,
        )
        project_7 = Project.objects.create(
            id=self.project_7_Id,
            hkrId=1111,
            name="Random name",
            description="Random desc",
            programmed=True,
            projectClass=masterClass_1,
            costForecast=600,
        )
        project_8 = Project.objects.create(
            id=self.project_8_Id,
            hkrId=1111,
            name="Random name",
            description="Random desc",
            programmed=True,
            projectClass=masterClass_2,
            costForecast=100,
        )
        ProjectFinancial.objects.create(
            project=project_1,
            budgetProposalCurrentYearPlus0=10,
            budgetProposalCurrentYearPlus1=50,
            budgetProposalCurrentYearPlus2=50,
            preliminaryCurrentYearPlus3=10,
            preliminaryCurrentYearPlus4=5,
            preliminaryCurrentYearPlus5=0,
            preliminaryCurrentYearPlus6=0,
            preliminaryCurrentYearPlus7=0,
            preliminaryCurrentYearPlus8=0,
            preliminaryCurrentYearPlus9=0,
            preliminaryCurrentYearPlus10=0,
        )
        ProjectFinancial.objects.create(
            project=project_2,
            budgetProposalCurrentYearPlus0=50,
            budgetProposalCurrentYearPlus1=50,
            budgetProposalCurrentYearPlus2=50,
            preliminaryCurrentYearPlus3=10,
            preliminaryCurrentYearPlus4=5,
            preliminaryCurrentYearPlus5=0,
            preliminaryCurrentYearPlus6=0,
            preliminaryCurrentYearPlus7=5,
            preliminaryCurrentYearPlus8=9,
            preliminaryCurrentYearPlus9=10,
            preliminaryCurrentYearPlus10=0,
        )

        ProjectFinancial.objects.create(
            project=project_3,
            budgetProposalCurrentYearPlus0=100,
            budgetProposalCurrentYearPlus1=50,
            budgetProposalCurrentYearPlus2=50,
            preliminaryCurrentYearPlus3=10,
            preliminaryCurrentYearPlus4=5,
            preliminaryCurrentYearPlus5=0,
            preliminaryCurrentYearPlus6=0,
            preliminaryCurrentYearPlus7=5,
            preliminaryCurrentYearPlus8=9,
            preliminaryCurrentYearPlus9=10,
            preliminaryCurrentYearPlus10=0,
        )
        ProjectFinancial.objects.create(
            project=project_4,
            budgetProposalCurrentYearPlus0=0,
            budgetProposalCurrentYearPlus1=0,
            budgetProposalCurrentYearPlus2=50,
            preliminaryCurrentYearPlus3=10,
            preliminaryCurrentYearPlus4=5,
            preliminaryCurrentYearPlus5=0,
            preliminaryCurrentYearPlus6=0,
            preliminaryCurrentYearPlus7=5,
            preliminaryCurrentYearPlus8=9,
            preliminaryCurrentYearPlus9=10,
            preliminaryCurrentYearPlus10=0,
        )
        ProjectFinancial.objects.create(
            project=project_5,
            budgetProposalCurrentYearPlus0=100,
            budgetProposalCurrentYearPlus1=50,
            budgetProposalCurrentYearPlus2=50,
            preliminaryCurrentYearPlus3=10,
            preliminaryCurrentYearPlus4=5,
            preliminaryCurrentYearPlus5=0,
            preliminaryCurrentYearPlus6=0,
            preliminaryCurrentYearPlus7=5,
            preliminaryCurrentYearPlus8=9,
            preliminaryCurrentYearPlus9=10,
            preliminaryCurrentYearPlus10=0,
        )
        ProjectFinancial.objects.create(
            project=project_6,
            budgetProposalCurrentYearPlus0=200,
            budgetProposalCurrentYearPlus1=50,
            budgetProposalCurrentYearPlus2=50,
            preliminaryCurrentYearPlus3=10,
            preliminaryCurrentYearPlus4=5,
            preliminaryCurrentYearPlus5=0,
            preliminaryCurrentYearPlus6=0,
            preliminaryCurrentYearPlus7=5,
            preliminaryCurrentYearPlus8=9,
            preliminaryCurrentYearPlus9=10,
            preliminaryCurrentYearPlus10=0,
        )
        ProjectFinancial.objects.create(
            project=project_7,
            budgetProposalCurrentYearPlus0=100,
            budgetProposalCurrentYearPlus1=50,
            budgetProposalCurrentYearPlus2=50,
            preliminaryCurrentYearPlus3=10,
            preliminaryCurrentYearPlus4=5,
            preliminaryCurrentYearPlus5=5,
            preliminaryCurrentYearPlus6=0,
            preliminaryCurrentYearPlus7=5,
            preliminaryCurrentYearPlus8=9,
            preliminaryCurrentYearPlus9=10,
            preliminaryCurrentYearPlus10=0,
        )
        ProjectFinancial.objects.create(
            project=project_8,
            budgetProposalCurrentYearPlus0=0,
            budgetProposalCurrentYearPlus1=0,
            budgetProposalCurrentYearPlus2=50,
            preliminaryCurrentYearPlus3=10,
            preliminaryCurrentYearPlus4=5,
            preliminaryCurrentYearPlus5=0,
            preliminaryCurrentYearPlus6=0,
            preliminaryCurrentYearPlus7=5,
            preliminaryCurrentYearPlus8=9,
            preliminaryCurrentYearPlus9=10,
            preliminaryCurrentYearPlus10=0,
        )

    def test_GET_class_with_sums(self):
        response = self.client.get(
            "/project-classes/{}/".format(self.projectMasterClass_1_Id)
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(response.json()["finances"]["year0"]["plannedBudget"], 560)
        self.assertEqual(response.json()["finances"]["year1"]["plannedBudget"], 300)
        self.assertEqual(response.json()["finances"]["year2"]["plannedBudget"], 300)
        self.assertEqual(response.json()["finances"]["year3"]["plannedBudget"], 60)
        self.assertEqual(response.json()["finances"]["year4"]["plannedBudget"], 30)
        self.assertEqual(response.json()["finances"]["year5"]["plannedBudget"], 5)
        self.assertEqual(response.json()["finances"]["year6"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year7"]["plannedBudget"], 25)
        self.assertEqual(response.json()["finances"]["year8"]["plannedBudget"], 45)
        self.assertEqual(response.json()["finances"]["year9"]["plannedBudget"], 50)
        self.assertEqual(response.json()["finances"]["year10"]["plannedBudget"], 0)

        response = self.client.get(
            "/project-classes/{}/".format(self.projectMasterClass_2_Id)
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(response.json()["finances"]["year0"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year1"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year2"]["plannedBudget"], 100)
        self.assertEqual(response.json()["finances"]["year3"]["plannedBudget"], 20)
        self.assertEqual(response.json()["finances"]["year4"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year5"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year6"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year7"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year8"]["plannedBudget"], 18)
        self.assertEqual(response.json()["finances"]["year9"]["plannedBudget"], 20)
        self.assertEqual(response.json()["finances"]["year10"]["plannedBudget"], 0)

        response = self.client.get(
            "/project-classes/{}/".format(self.projectClass_1_Id)
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(response.json()["finances"]["year0"]["plannedBudget"], 260)
        self.assertEqual(response.json()["finances"]["year1"]["plannedBudget"], 200)
        self.assertEqual(response.json()["finances"]["year2"]["plannedBudget"], 200)
        self.assertEqual(response.json()["finances"]["year3"]["plannedBudget"], 40)
        self.assertEqual(response.json()["finances"]["year4"]["plannedBudget"], 20)
        self.assertEqual(response.json()["finances"]["year5"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year6"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year7"]["plannedBudget"], 15)
        self.assertEqual(response.json()["finances"]["year8"]["plannedBudget"], 27)
        self.assertEqual(response.json()["finances"]["year9"]["plannedBudget"], 30)
        self.assertEqual(response.json()["finances"]["year10"]["plannedBudget"], 0)

        response = self.client.get(
            "/project-classes/{}/".format(self.projectSubClass_1_Id)
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(response.json()["finances"]["year0"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year1"]["plannedBudget"], 50)
        self.assertEqual(response.json()["finances"]["year2"]["plannedBudget"], 50)
        self.assertEqual(response.json()["finances"]["year3"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year4"]["plannedBudget"], 5)
        self.assertEqual(response.json()["finances"]["year5"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year6"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year7"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year8"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year9"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year10"]["plannedBudget"], 0)

        response = self.client.get(
            "/project-classes/{}/".format(self.projectSubClass_2_Id)
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(response.json()["finances"]["year0"]["plannedBudget"], 100)
        self.assertEqual(response.json()["finances"]["year1"]["plannedBudget"], 50)
        self.assertEqual(response.json()["finances"]["year2"]["plannedBudget"], 50)
        self.assertEqual(response.json()["finances"]["year3"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year4"]["plannedBudget"], 5)
        self.assertEqual(response.json()["finances"]["year5"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year6"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year7"]["plannedBudget"], 5)
        self.assertEqual(response.json()["finances"]["year8"]["plannedBudget"], 9)
        self.assertEqual(response.json()["finances"]["year9"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year10"]["plannedBudget"], 0)

    def test_GET_location_with_sums(self):
        response = self.client.get(
            "/project-locations/{}/".format(self.projectDistrict_1_Id)
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(response.json()["finances"]["year0"]["plannedBudget"], 60)
        self.assertEqual(response.json()["finances"]["year1"]["plannedBudget"], 100)
        self.assertEqual(response.json()["finances"]["year2"]["plannedBudget"], 150)
        self.assertEqual(response.json()["finances"]["year3"]["plannedBudget"], 30)
        self.assertEqual(response.json()["finances"]["year4"]["plannedBudget"], 15)
        self.assertEqual(response.json()["finances"]["year5"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year6"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year7"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year8"]["plannedBudget"], 18)
        self.assertEqual(response.json()["finances"]["year9"]["plannedBudget"], 20)
        self.assertEqual(response.json()["finances"]["year10"]["plannedBudget"], 0)

        response = self.client.get(
            "/project-locations/{}/".format(self.projectDistrict_2_Id)
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(response.json()["finances"]["year0"]["plannedBudget"], 100)
        self.assertEqual(response.json()["finances"]["year1"]["plannedBudget"], 50)
        self.assertEqual(response.json()["finances"]["year2"]["plannedBudget"], 50)
        self.assertEqual(response.json()["finances"]["year3"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year4"]["plannedBudget"], 5)
        self.assertEqual(response.json()["finances"]["year5"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year6"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year7"]["plannedBudget"], 5)
        self.assertEqual(response.json()["finances"]["year8"]["plannedBudget"], 9)
        self.assertEqual(response.json()["finances"]["year9"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year10"]["plannedBudget"], 0)

    def test_GET_group_with_sums(self):
        response = self.client.get("/project-groups/{}/".format(self.projectGroup_1_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(response.json()["finances"]["projectBudgets"], 600)
        self.assertEqual(response.json()["finances"]["year0"]["plannedBudget"], 160)
        self.assertEqual(response.json()["finances"]["year1"]["plannedBudget"], 150)
        self.assertEqual(response.json()["finances"]["year2"]["plannedBudget"], 150)
        self.assertEqual(response.json()["finances"]["year3"]["plannedBudget"], 30)
        self.assertEqual(response.json()["finances"]["year4"]["plannedBudget"], 15)
        self.assertEqual(response.json()["finances"]["year5"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year6"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year7"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year8"]["plannedBudget"], 18)
        self.assertEqual(response.json()["finances"]["year9"]["plannedBudget"], 20)
        self.assertEqual(response.json()["finances"]["year10"]["plannedBudget"], 0)

        response = self.client.get("/project-groups/{}/".format(self.projectGroup_2_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(response.json()["finances"]["projectBudgets"], 100)
        self.assertEqual(response.json()["finances"]["year0"]["plannedBudget"], 100)
        self.assertEqual(response.json()["finances"]["year1"]["plannedBudget"], 50)
        self.assertEqual(response.json()["finances"]["year2"]["plannedBudget"], 50)
        self.assertEqual(response.json()["finances"]["year3"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year4"]["plannedBudget"], 5)
        self.assertEqual(response.json()["finances"]["year5"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year6"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year7"]["plannedBudget"], 5)
        self.assertEqual(response.json()["finances"]["year8"]["plannedBudget"], 9)
        self.assertEqual(response.json()["finances"]["year9"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year10"]["plannedBudget"], 0)

        response = self.client.get("/project-groups/{}/".format(self.projectGroup_3_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(response.json()["finances"]["projectBudgets"], 100)
        self.assertEqual(response.json()["finances"]["year0"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year1"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year2"]["plannedBudget"], 50)
        self.assertEqual(response.json()["finances"]["year3"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year4"]["plannedBudget"], 5)
        self.assertEqual(response.json()["finances"]["year5"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year6"]["plannedBudget"], 0)
        self.assertEqual(response.json()["finances"]["year7"]["plannedBudget"], 5)
        self.assertEqual(response.json()["finances"]["year8"]["plannedBudget"], 9)
        self.assertEqual(response.json()["finances"]["year9"]["plannedBudget"], 10)
        self.assertEqual(response.json()["finances"]["year10"]["plannedBudget"], 0)
