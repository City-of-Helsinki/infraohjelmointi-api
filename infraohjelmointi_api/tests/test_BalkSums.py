from datetime import date
from django.test import TestCase
from infraohjelmointi_api.models import (
    Project,
    ProjectClass,
    ProjectFinancial,
    ProjectGroup,
    ProjectLocation,
)

import uuid
from infraohjelmointi_api.models.AppStateValueModel import AppStateValue
from overrides import override

from infraohjelmointi_api.views import BaseViewSet
from unittest.mock import patch


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
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
    projectCoordinationDistrict_1_Id = uuid.UUID("2b9e7879-09a5-4257-93c6-cd20b75e6904")
    projectCoordinatorMasterClass_1_Id = uuid.UUID(
        "0f0c982c-049f-4ec5-b6a4-bd43a5cf8f65"
    )
    projectCoordinatorClass_1_Id = uuid.UUID("74f1a8a0-7bf9-4d1d-9cf4-da58825fac4d")
    projectCoordinatorSubClass_1_Id = uuid.UUID("ee223e27-8913-4194-82d9-6c6698d7c12c")
    coordinatorCollectiveSubLevel_1_Id = uuid.UUID(
        "b7b88072-d6c7-4831-9c0c-25cd84307a08"
    )

    # Helper function to test values
    def runFinancesAssertTests(self, response, index, name, values):
        for i in range(0, 11):
            year_key = "year{}".format(i)

            if index != None:
                data = response.json()[index]["finances"]
                self.assertEqual(data[year_key][name], values[i])
            else:
                data = response.json()["finances"]
                self.assertEqual(data[year_key][name], values[i])

    @classmethod
    @override
    def setUpTestData(self):
        year = date.today().year

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
        district_3 = ProjectLocation.objects.create(
            id=self.projectDistrict_3_Id,
            name="District 3",
            parent=None,
            path="District 3",
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
        masterClass_3 = ProjectClass.objects.create(
            id=self.projectMasterClass_3_Id,
            name="Master Class 3",
            parent=None,
            path="Master Class 3",
        )
        _class = masterClass_1.childClass.create(
            name="Test Class 1",
            id=self.projectClass_1_Id,
            path="Master Class 1/Test Class 1",
        )
        _class_2 = masterClass_3.childClass.create(
            name="Test Class 2",
            id=self.projectClass_2_Id,
            path="Master Class 3/Test Class 1",
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
        projectGroup_1 = ProjectGroup.objects.create(
            id=self.projectGroup_1_Id,
            name="Test Group 1 rain",
            locationRelation=district_1
        )
        projectGroup_2 = ProjectGroup.objects.create(
            id=self.projectGroup_2_Id, name="Test Group 2"
        )
        projectGroup_3 = ProjectGroup.objects.create(
            id=self.projectGroup_3_Id, name="Test Group 3 park"
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
        project_9 = Project.objects.create(
            id=self.project_9_Id,
            hkrId=1111,
            name="Random name",
            description="Random desc",
            programmed=True,
            projectLocation=district_3,
            projectClass=_class_2,
            costForecast=100,
        )
        # for project_1
        ProjectFinancial.objects.create(project=project_1, year=year, value=10)
        ProjectFinancial.objects.create(project=project_1, year=year + 1, value=50)
        ProjectFinancial.objects.create(project=project_1, year=year + 2, value=50)
        ProjectFinancial.objects.create(project=project_1, year=year + 3, value=10)
        ProjectFinancial.objects.create(project=project_1, year=year + 4, value=5)
        ProjectFinancial.objects.create(project=project_1, year=year + 5, value=0)
        ProjectFinancial.objects.create(project=project_1, year=year + 6, value=0)
        ProjectFinancial.objects.create(project=project_1, year=year + 7, value=0)
        ProjectFinancial.objects.create(project=project_1, year=year + 8, value=0)
        ProjectFinancial.objects.create(project=project_1, year=year + 9, value=0)
        ProjectFinancial.objects.create(project=project_1, year=year + 10, value=0)

        # for project_2
        ProjectFinancial.objects.create(project=project_2, year=year, value=50)
        ProjectFinancial.objects.create(project=project_2, year=year + 1, value=50)
        ProjectFinancial.objects.create(project=project_2, year=year + 2, value=50)
        ProjectFinancial.objects.create(project=project_2, year=year + 3, value=10)
        ProjectFinancial.objects.create(project=project_2, year=year + 4, value=5)
        ProjectFinancial.objects.create(project=project_2, year=year + 5, value=0)
        ProjectFinancial.objects.create(project=project_2, year=year + 6, value=0)
        ProjectFinancial.objects.create(project=project_2, year=year + 7, value=5)
        ProjectFinancial.objects.create(project=project_2, year=year + 8, value=9)
        ProjectFinancial.objects.create(project=project_2, year=year + 9, value=10)
        ProjectFinancial.objects.create(project=project_2, year=year + 10, value=0)

        # for project_3
        ProjectFinancial.objects.create(project=project_3, year=year, value=100)
        ProjectFinancial.objects.create(project=project_3, year=year + 1, value=50)
        ProjectFinancial.objects.create(project=project_3, year=year + 2, value=50)
        ProjectFinancial.objects.create(project=project_3, year=year + 3, value=10)
        ProjectFinancial.objects.create(project=project_3, year=year + 4, value=5)
        ProjectFinancial.objects.create(project=project_3, year=year + 5, value=0)
        ProjectFinancial.objects.create(project=project_3, year=year + 6, value=0)
        ProjectFinancial.objects.create(project=project_3, year=year + 7, value=5)
        ProjectFinancial.objects.create(project=project_3, year=year + 8, value=9)
        ProjectFinancial.objects.create(project=project_3, year=year + 9, value=10)
        ProjectFinancial.objects.create(project=project_3, year=year + 10, value=0)

        # for project_4
        ProjectFinancial.objects.create(project=project_4, year=year, value=0)
        ProjectFinancial.objects.create(project=project_4, year=year + 1, value=0)
        ProjectFinancial.objects.create(project=project_4, year=year + 2, value=50)
        ProjectFinancial.objects.create(project=project_4, year=year + 3, value=10)
        ProjectFinancial.objects.create(project=project_4, year=year + 4, value=5)
        ProjectFinancial.objects.create(project=project_4, year=year + 5, value=0)
        ProjectFinancial.objects.create(project=project_4, year=year + 6, value=0)
        ProjectFinancial.objects.create(project=project_4, year=year + 7, value=5)
        ProjectFinancial.objects.create(project=project_4, year=year + 8, value=9)
        ProjectFinancial.objects.create(project=project_4, year=year + 9, value=10)
        ProjectFinancial.objects.create(project=project_4, year=year + 10, value=0)

        # for project_5
        ProjectFinancial.objects.create(project=project_5, year=year, value=100)
        ProjectFinancial.objects.create(project=project_5, year=year + 1, value=50)
        ProjectFinancial.objects.create(project=project_5, year=year + 2, value=50)
        ProjectFinancial.objects.create(project=project_5, year=year + 3, value=10)
        ProjectFinancial.objects.create(project=project_5, year=year + 4, value=5)
        ProjectFinancial.objects.create(project=project_5, year=year + 5, value=0)
        ProjectFinancial.objects.create(project=project_5, year=year + 6, value=0)
        ProjectFinancial.objects.create(project=project_5, year=year + 7, value=5)
        ProjectFinancial.objects.create(project=project_5, year=year + 8, value=9)
        ProjectFinancial.objects.create(project=project_5, year=year + 9, value=10)
        ProjectFinancial.objects.create(project=project_5, year=year + 10, value=0)

        # for project_6
        ProjectFinancial.objects.create(project=project_6, year=year, value=200)
        ProjectFinancial.objects.create(project=project_6, year=year + 1, value=50)
        ProjectFinancial.objects.create(project=project_6, year=year + 2, value=50)
        ProjectFinancial.objects.create(project=project_6, year=year + 3, value=10)
        ProjectFinancial.objects.create(project=project_6, year=year + 4, value=5)
        ProjectFinancial.objects.create(project=project_6, year=year + 5, value=0)
        ProjectFinancial.objects.create(project=project_6, year=year + 6, value=0)
        ProjectFinancial.objects.create(project=project_6, year=year + 7, value=5)
        ProjectFinancial.objects.create(project=project_6, year=year + 8, value=9)
        ProjectFinancial.objects.create(project=project_6, year=year + 9, value=10)
        ProjectFinancial.objects.create(project=project_6, year=year + 10, value=0)

        # for project_7
        ProjectFinancial.objects.create(project=project_7, year=year, value=100)
        ProjectFinancial.objects.create(project=project_7, year=year + 1, value=50)
        ProjectFinancial.objects.create(project=project_7, year=year + 2, value=50)
        ProjectFinancial.objects.create(project=project_7, year=year + 3, value=10)
        ProjectFinancial.objects.create(project=project_7, year=year + 4, value=5)
        ProjectFinancial.objects.create(project=project_7, year=year + 5, value=5)
        ProjectFinancial.objects.create(project=project_7, year=year + 6, value=0)
        ProjectFinancial.objects.create(project=project_7, year=year + 7, value=5)
        ProjectFinancial.objects.create(project=project_7, year=year + 8, value=9)
        ProjectFinancial.objects.create(project=project_7, year=year + 9, value=10)
        ProjectFinancial.objects.create(project=project_7, year=year + 10, value=0)

        # for project_8
        ProjectFinancial.objects.create(project=project_8, year=year, value=0)
        ProjectFinancial.objects.create(project=project_8, year=year + 1, value=0)
        ProjectFinancial.objects.create(project=project_8, year=year + 2, value=50)
        ProjectFinancial.objects.create(project=project_8, year=year + 3, value=10)
        ProjectFinancial.objects.create(project=project_8, year=year + 4, value=5)
        ProjectFinancial.objects.create(project=project_8, year=year + 5, value=0)
        ProjectFinancial.objects.create(project=project_8, year=year + 6, value=0)
        ProjectFinancial.objects.create(project=project_8, year=year + 7, value=5)
        ProjectFinancial.objects.create(project=project_8, year=year + 8, value=9)
        ProjectFinancial.objects.create(project=project_8, year=year + 9, value=10)
        ProjectFinancial.objects.create(project=project_8, year=year + 10, value=0)

        # for project_9
        ProjectFinancial.objects.create(project=project_9, year=year, value=100)
        ProjectFinancial.objects.create(project=project_9, year=year + 1, value=50)
        ProjectFinancial.objects.create(project=project_9, year=year + 2, value=50)
        ProjectFinancial.objects.create(project=project_9, year=year + 3, value=10)
        ProjectFinancial.objects.create(project=project_9, year=year + 4, value=5)
        ProjectFinancial.objects.create(project=project_9, year=year + 5, value=5)
        ProjectFinancial.objects.create(project=project_9, year=year + 6, value=0)
        ProjectFinancial.objects.create(project=project_9, year=year + 7, value=5)
        ProjectFinancial.objects.create(project=project_9, year=year + 8, value=9)
        ProjectFinancial.objects.create(project=project_9, year=year + 9, value=10)
        ProjectFinancial.objects.create(project=project_9, year=year + 10, value=0)

        ##### Frame Financials #####
        # for project_1
        ProjectFinancial.objects.create(
            project=project_1, year=year, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_1, year=year + 1, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_1, year=year + 2, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_1, year=year + 3, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_1, year=year + 4, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_1, year=year + 5, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_1, year=year + 6, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_1, year=year + 7, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_1, year=year + 8, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_1, year=year + 9, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_1, year=year + 10, value=0, forFrameView=True
        )

        # for project_2
        ProjectFinancial.objects.create(
            project=project_2, year=year, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_2, year=year + 1, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_2, year=year + 2, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_2, year=year + 3, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_2, year=year + 4, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_2, year=year + 5, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_2, year=year + 6, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_2, year=year + 7, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_2, year=year + 8, value=9, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_2, year=year + 9, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_2, year=year + 10, value=0, forFrameView=True
        )

        # for project_3
        ProjectFinancial.objects.create(
            project=project_3, year=year, value=500, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_3, year=year + 1, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_3, year=year + 2, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_3, year=year + 3, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_3, year=year + 4, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_3, year=year + 5, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_3, year=year + 6, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_3, year=year + 7, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_3, year=year + 8, value=9, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_3, year=year + 9, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_3, year=year + 10, value=0, forFrameView=True
        )

        # for project_4
        ProjectFinancial.objects.create(
            project=project_4, year=year, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_4, year=year + 1, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_4, year=year + 2, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_4, year=year + 3, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_4, year=year + 4, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_4, year=year + 5, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_4, year=year + 6, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_4, year=year + 7, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_4, year=year + 8, value=9, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_4, year=year + 9, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_4, year=year + 10, value=0, forFrameView=True
        )

        # for project_5
        ProjectFinancial.objects.create(
            project=project_5, year=year, value=500, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_5, year=year + 1, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_5, year=year + 2, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_5, year=year + 3, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_5, year=year + 4, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_5, year=year + 5, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_5, year=year + 6, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_5, year=year + 7, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_5, year=year + 8, value=9, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_5, year=year + 9, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_5, year=year + 10, value=0, forFrameView=True
        )

        # for project_6
        ProjectFinancial.objects.create(
            project=project_6, year=year, value=200, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_6, year=year + 1, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_6, year=year + 2, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_6, year=year + 3, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_6, year=year + 4, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_6, year=year + 5, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_6, year=year + 6, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_6, year=year + 7, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_6, year=year + 8, value=9, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_6, year=year + 9, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_6, year=year + 10, value=0, forFrameView=True
        )

        # for project_7
        ProjectFinancial.objects.create(
            project=project_7, year=year, value=500, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_7, year=year + 1, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_7, year=year + 2, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_7, year=year + 3, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_7, year=year + 4, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_7, year=year + 5, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_7, year=year + 6, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_7, year=year + 7, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_7, year=year + 8, value=9, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_7, year=year + 9, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_7, year=year + 10, value=0, forFrameView=True
        )

        # for project_8
        ProjectFinancial.objects.create(
            project=project_8, year=year, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_8, year=year + 1, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_8, year=year + 2, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_8, year=year + 3, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_8, year=year + 4, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_8, year=year + 5, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_8, year=year + 6, value=0, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_8, year=year + 7, value=5, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_8, year=year + 8, value=9, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_8, year=year + 9, value=50, forFrameView=True
        )
        ProjectFinancial.objects.create(
            project=project_8, year=year + 10, value=0, forFrameView=True
        )

        # Coordinator projects, classes/locations

        coordinatorMasterClass_1 = ProjectClass.objects.create(
            id=self.projectCoordinatorMasterClass_1_Id,
            name="Coordinator Master Class 1",
            parent=None,
            path="Coordinator Master Class 1",
            forCoordinatorOnly=True,
            relatedTo=masterClass_1,
        )
        coordinatorMasterClass_1.finances.create(
            frameBudget=100, budgetChange=100, year=year
        )
        coordinatorMasterClass_1.finances.create(
            frameBudget=100, budgetChange=100, year=year, forFrameView=True
        )
        coordinatorMasterClass_1.finances.create(
            frameBudget=50, budgetChange=50, year=year + 1
        )
        coordinatorMasterClass_1.finances.create(
            frameBudget=50, budgetChange=50, year=year + 1, forFrameView=True
        )

        coordinatorClass_1 = coordinatorMasterClass_1.childClass.create(
            name="Coordinator Test Class 1",
            id=self.projectCoordinatorClass_1_Id,
            path="Coordinator Master Class 1/Coordinator Test Class 1",
            forCoordinatorOnly=True,
            relatedTo=_class,
        )
        coordinatorClass_1.finances.create(frameBudget=2000, budgetChange=50, year=year)
        coordinatorClass_1.finances.create(frameBudget=2000, budgetChange=50, year=year, forFrameView=True)
        coordinatorSubClass_1 = coordinatorClass_1.childClass.create(
            id=self.projectCoordinatorSubClass_1_Id,
            name="Coordinator Sub class 1",
            path="Coordinator Master Class 1/Coordinator Test Class 1/Coordinator Sub class 1",
            forCoordinatorOnly=True,
            relatedTo=subClass_1,
        )
        coordinatorSubClass_1.childClass.create(
            id=self.coordinatorCollectiveSubLevel_1_Id,
            name="collective sub level",
            path="Coordinator Master Class 1/Coordinator Test Class 1/Coordinator Sub class 1/collective sub level",
            forCoordinatorOnly=True,
            relatedTo=None,
        )

        coordinatorSubClass_1.finances.create(
            frameBudget=0, budgetChange=50, year=year + 5
        )

        coordinatorSubClass_1.finances.create(
            frameBudget=0, budgetChange=50, year=year + 5, forFrameView=True
        )

        projectCoordinationDistrict_1 = ProjectLocation.objects.create(
            id=self.projectCoordinationDistrict_1_Id,
            name="Coordinator district 1",
            parent=None,
            path="Coordinator district 1",
            forCoordinatorOnly=True,
            parentClass=coordinatorSubClass_1,
            relatedTo=district_1,
        )
        projectCoordinationDistrict_1.finances.create(
            frameBudget=200, budgetChange=0, year=year
        )

    def test_GET_class_with_sums(self):
        response = self.client.get("/project-classes/{}/".format(self.projectMasterClass_1_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(response.json()["finances"]["year0"]["isFrameBudgetOverlap"], True)

        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[460,250,250,50,25,5,0,20,36,40,0])
        self.runFinancesAssertTests(response, index=None, name="frameBudget", values=[100,50,0,0,0,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=None, name="budgetChange", values=[100,50,0,0,0,0,0,0,0,0,0])

        response = self.client.get("/project-classes/{}/".format(self.projectMasterClass_2_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[0,0,50,10,5,0,0,5,9,10,0])
        self.runFinancesAssertTests(response, index=None, name="frameBudget", values=[0,0,0,0,0,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=None, name="budgetChange", values=[0,0,0,0,0,0,0,0,0,0,0])

        response = self.client.get("/project-classes/{}/".format(self.projectClass_1_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[160,150,150,30,15,0,0,10,18,20,0])
        self.runFinancesAssertTests(response, index=None, name="frameBudget", values=[2000,0,0,0,0,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=None, name="budgetChange", values=[50,0,0,0,0,0,0,0,0,0,0])

        response = self.client.get("/project-classes/{}/".format(self.projectSubClass_1_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[10,50,50,10,5,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=None, name="frameBudget", values=[0,0,0,0,0,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=None, name="budgetChange", values=[0,0,0,0,0,50,0,0,0,0,0])

        response = self.client.get("/project-classes/{}/".format(self.projectSubClass_2_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.runFinancesAssertTests(response, index=None, name="budgetChange", values=[0,0,0,0,0,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=None, name="frameBudget", values=[0,0,0,0,0,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[0,0,0,0,0,0,0,0,0,0,0])


    def test_GET_coordinator_class_with_sums(self):
        response = self.client.get("/project-classes/coordinator/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(len(response.json()), 4, msg="Number of coordinator classes != 4")

        # Sum for coordinator masterClass, it will miss project 3 as it uses subClass 2 which has no coordination class
        self.assertEqual(response.json()[0]["id"], self.projectCoordinatorMasterClass_1_Id.__str__())
        self.assertEqual(response.json()[0]["finances"]["year0"]["isFrameBudgetOverlap"], True)

        self.runFinancesAssertTests(response, index=0, name="plannedBudget", values=[460,250,250,50,25,5,0,20,36,40,0])
        self.runFinancesAssertTests(response, index=0, name="budgetChange", values=[100,50,0,0,0,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=0, name="frameBudget", values=[100,50,0,0,0,0,0,0,0,0,0])

        self.assertEqual(response.json()[1]["id"], self.projectCoordinatorClass_1_Id.__str__())
        self.assertEqual(response.json()[1]["finances"]["year0"]["isFrameBudgetOverlap"], False)

        self.runFinancesAssertTests(response, index=1, name="plannedBudget", values=[160,150,150,30,15,0,0,10,18,20,0])
        self.runFinancesAssertTests(response, index=1, name="frameBudget", values=[2000,0,0,0,0,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=1, name="budgetChange", values=[50,0,0,0,0,0,0,0,0,0,0])

        self.assertEqual(response.json()[2]["id"], self.projectCoordinatorSubClass_1_Id.__str__())
        self.assertEqual(response.json()[2]["finances"]["year0"]["isFrameBudgetOverlap"], True)

        self.runFinancesAssertTests(response, index=2, name="plannedBudget", values=[10,50,50,10,5,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=2, name="budgetChange", values=[0,0,0,0,0,50,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=2, name="frameBudget", values=[0,0,0,0,0,0,0,0,0,0,0])

        #### with frame view financial sums ####
        response = self.client.get("/project-classes/coordinator/?forcedToFrame=true")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(len(response.json()), 4, msg="Number of coordinator classes != 4")

        # Sum for coordinator masterClass, it will miss project 3 as it uses subClass 2 which has no coordination class
        self.assertEqual(response.json()[0]["id"], self.projectCoordinatorMasterClass_1_Id.__str__())
        self.assertEqual(response.json()[0]["finances"]["year0"]["isFrameBudgetOverlap"], True)

        self.runFinancesAssertTests(response, index=0, name="plannedBudget", values=[1300,250,250,250,25,5,0,20,36,200,0])
        self.runFinancesAssertTests(response, index=0, name="budgetChange", values=[100,50,0,0,0,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=0, name="frameBudget", values=[100,50,0,0,0,0,0,0,0,0,0])

        self.assertEqual(response.json()[1]["id"], self.projectCoordinatorClass_1_Id.__str__())

        self.runFinancesAssertTests(response, index=1, name="plannedBudget", values=[600,150,150,150,15,0,0,10,18,100,0])
        self.runFinancesAssertTests(response, index=1, name="frameBudget", values=[2000,0,0,0,0,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=1, name="budgetChange", values=[50,0,0,0,0,0,0,0,0,0,0])

        self.assertEqual(response.json()[2]["id"], self.projectCoordinatorSubClass_1_Id.__str__())

        self.runFinancesAssertTests(response, index=2, name="plannedBudget", values=[50,50,50,50,5,0,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=2, name="budgetChange", values=[0,0,0,0,0,50,0,0,0,0,0])
        self.runFinancesAssertTests(response, index=2, name="frameBudget", values=[0,0,0,0,0,0,0,0,0,0,0])

    def test_PATCH_coordinator_class_finances(self):
        response = self.client.patch(
            "/project-classes/coordinator/{}/".format(
                self.projectCoordinatorMasterClass_1_Id.__str__()
            ),
            data={
                "finances": {
                    "year": date.today().year,
                    "year0": {"frameBudget": 1000, "budgetChange": 50},
                },
                "forcedToFrame": False
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(response.json()["finances"]["year0"]["frameBudget"], 1000)
        self.assertEqual(response.json()["finances"]["year0"]["budgetChange"], 50)

        # Check same finances reflect on the related planning class
        response = self.client.get("/project-classes/{}/".format(self.projectMasterClass_1_Id))

        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(response.json()["finances"]["year0"]["frameBudget"], 1000)
        self.assertEqual(response.json()["finances"]["year0"]["budgetChange"], 50)

    def test_GET_location_with_sums(self):
        response = self.client.get(
            "/project-locations/{}/".format(self.projectDistrict_1_Id)
        )

        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(response.json()["finances"]["year0"]["frameBudget"], 200)

        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[60,100,100,20,10,0,0,5,9,10,0])

        response = self.client.get("/project-locations/{}/".format(self.projectDistrict_2_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[0,0,0,0,0,0,0,0,0,0,0])

        response = self.client.get("/project-locations/{}/".format(self.projectDistrict_3_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[100,50,50,10,5,5,0,5,9,10,0])

    def test_GET_coordinator_location_with_sums(self):
        response = self.client.get("/project-locations/coordinator/")

        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(len(response.json()), 1, msg="Number of coordinator locations != 1")
        self.assertEqual(response.json()[0]["id"], self.projectCoordinationDistrict_1_Id.__str__())

        self.assertEqual(response.json()[0]["finances"]["year0"]["frameBudget"], 200)
        self.runFinancesAssertTests(response, index=0, name="plannedBudget", values=[60,100,100,20,10,0,0,5,9,10,0])

        #### Frame view financial sums ####
        response = self.client.get("/project-locations/coordinator/?forcedToFrame=true")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(len(response.json()), 1, msg="Number of coordinator locations != 1")
        self.assertEqual(response.json()[0]["id"], self.projectCoordinationDistrict_1_Id.__str__())

        self.runFinancesAssertTests(response, index=0, name="plannedBudget", values=[100,100,100,100,10,0,0,5,9,50,0])

    def test_PATCH_coordinator_location_finances(self):
        response = self.client.patch(
            "/project-locations/coordinator/{}/".format(
                self.projectCoordinationDistrict_1_Id.__str__()
            ),
            data={
                "finances": {
                    "year": date.today().year,
                    "year0": {"frameBudget": 1000, "budgetChange": 50},
                },
                "forcedToFrame": False
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(response.json()["finances"]["year0"]["frameBudget"], 1000)
        self.assertEqual(response.json()["finances"]["year0"]["budgetChange"], 50)

        # Chcek same finances reflect on the related planning district
        response = self.client.get("/project-locations/{}/".format(self.projectDistrict_1_Id))

        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(response.json()["finances"]["year0"]["frameBudget"], 1000)
        self.assertEqual(response.json()["finances"]["year0"]["budgetChange"], 50)

    def test_GET_group_with_sums(self):
        response = self.client.get("/project-groups/{}/".format(self.projectGroup_1_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(response.json()["finances"]["projectBudgets"], 600)

        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[160,150,150,30,15,0,0,10,18,20,0])

        # Projects under projectGroup 3 and 2 are not programmed hence all sums are 0
        response = self.client.get("/project-groups/{}/".format(self.projectGroup_2_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(response.json()["finances"]["projectBudgets"], 0)

        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[0,0,0,0,0,0,0,0,0,0,0])

        response = self.client.get("/project-groups/{}/".format(self.projectGroup_3_Id))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(response.json()["finances"]["projectBudgets"], 0)

        self.runFinancesAssertTests(response, index=None, name="plannedBudget", values=[0,0,0,0,0,0,0,0,0,0,0])
