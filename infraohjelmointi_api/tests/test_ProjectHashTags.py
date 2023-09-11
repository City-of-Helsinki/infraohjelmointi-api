from django.test import TestCase
from rest_framework.renderers import JSONRenderer
from infraohjelmointi_api.models import ProjectHashTag, Project
from infraohjelmointi_api.serializers import ProjectHashtagSerializer
import uuid
from overrides import override
from infraohjelmointi_api.views import BaseViewSet
from unittest.mock import patch


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectHashTagTestCase(TestCase):
    project_1_Id = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")
    project_2_Id = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    project_3_Id = uuid.UUID("fdc89f56-b631-4109-a137-45b950de6b10")
    project_4_Id = uuid.UUID("7c5b981e-286f-4065-9d9e-29d8d1714e4c")
    project_5_Id = uuid.UUID("441d80e1-9ab1-4b35-91cc-6017ea308d87")
    project_6_Id = uuid.UUID("90852adc-d47e-4fd9-944f-cb8d36076c21")
    projectHashTag_1_Id = uuid.UUID("e4d7b4b0-830d-4310-8b29-3c7d1e3132ba")
    projectHashTag_2_Id = uuid.UUID("eb8635b3-4e83-45d9-a1af-6bc49bf2aeb7")
    projectHashTag_3_Id = uuid.UUID("35765b82-cd07-4411-a664-97ac17b40531")
    projectHashTag_4_Id = uuid.UUID("60d0c256-68b9-49ae-874b-23960fd38910")

    @classmethod
    @override
    def setUpTestData(self):
        self.projectHashTag_1 = ProjectHashTag.objects.create(
            id=self.projectHashTag_1_Id, value="Hashtag 1", archived=False
        )
        self.projectHashTag_2 = ProjectHashTag.objects.create(
            id=self.projectHashTag_2_Id, value="Hashtag 2", archived=False
        )
        self.projectHashTag_3 = ProjectHashTag.objects.create(
            id=self.projectHashTag_3_Id, value="Hashtag 3", archived=False
        )

    def test_HashTag_is_created(self):
        self.assertEqual(
            ProjectHashTag.objects.filter(id=self.projectHashTag_1_Id).exists(),
            True,
            msg="Created hashTag with Id {} does not exist in DB".format(
                self.projectHashTag_1_Id
            ),
        )
        hashTag_1 = ProjectHashTag.objects.get(id=self.projectHashTag_1_Id)
        self.assertIsInstance(
            hashTag_1,
            ProjectHashTag,
            msg="Object retrieved from DB != typeof ProjectHashTag",
        )
        self.assertEqual(
            hashTag_1.id,
            self.projectHashTag_1.id,
            msg="Object from DB != created Object",
        )

    def test_GET_all_HashTags(self):
        response = self.client.get("/project-hashtags/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        # 26 HashTags -> 23 already from data population migration + 3 just created
        self.assertEqual(
            len(response.json()["hashTags"]),
            26,
            msg="Number of returned HashTags != 26",
        )
        ProjectHashTag.objects.create(id=self.projectHashTag_4_Id, value="Hashtag 4")
        response = self.client.get("/project-hashtags/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(
            len(response.json()["hashTags"]),
            27,
            msg="Number of returned HashTags != 27",
        )

    def test_GET_one_HashTag(self):
        response = self.client.get(
            "/project-hashtags/{}/".format(self.projectHashTag_1_Id)
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        # serialize the model instances
        serializer = ProjectHashtagSerializer(
            ProjectHashTag.objects.get(id=self.projectHashTag_1_Id), many=False
        )

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected

        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(response.content, result_expected)

    def test_POST_HashTag(self):
        data = {"value": "POST HashTag"}
        response = self.client.post(
            "/project-hashtags/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201, msg="Status code != 201")
        new_createdId = response.json()["id"]
        self.assertEqual(
            ProjectHashTag.objects.filter(id=new_createdId).exists(),
            True,
            msg="HashTag created using POST request does not exist in DB",
        )

    def test_PATCH_HashTag(self):
        data = {"value": "PATCH HashTag"}
        response = self.client.patch(
            "/project-hashtags/{}/".format(self.projectHashTag_1_Id),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["value"],
            data["value"],
            msg="Data not updated in the DB",
        )

    def test_DELETE_HashTag(self):
        response = self.client.delete(
            "/project-hashtags/{}/".format(self.projectHashTag_1_Id)
        )
        self.assertEqual(
            response.status_code,
            204,
            msg="Error deleting HashTag with Id {}".format(self.projectHashTag_1_Id),
        )
        self.assertEqual(
            ProjectHashTag.objects.filter(id=self.projectHashTag_1_Id).exists(),
            False,
            msg="HashTag with Id {} still exists in DB".format(
                self.projectHashTag_1_Id
            ),
        )

    def test_popular_HashTags(self):
        response = self.client.get("/project-hashtags/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(
            len(response.json()["popularHashTags"]),
            0,
            msg="Number of popular hashTags != 0, but hashTags have yet been used",
        )
        project_1 = Project.objects.create(
            id=self.project_1_Id,
            name="Test Project 1",
            description="Test Description 1",
        )
        project_1.hashTags.add(self.projectHashTag_1, self.projectHashTag_2)
        project_2 = Project.objects.create(
            id=self.project_2_Id,
            name="Test Project 2",
            description="Test Description 2",
        )
        project_2.hashTags.add(self.projectHashTag_1, self.projectHashTag_3)

        response = self.client.get("/project-hashtags/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(
            response.json()["popularHashTags"][0]["value"],
            self.projectHashTag_1.value,
            msg="HashTag with Id {} is not the most popular hashTag but is used the most".format(
                self.projectHashTag_1_Id
            ),
        )

        response = self.client.get(
            "/project-hashtags/{}/".format(self.projectHashTag_1_Id.__str__())
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(
            response.json()["usageCount"],
            2,
            msg="HashTag usageCount != 2",
        )

        project_2.hashTags.remove(self.projectHashTag_1)
        project_2.hashTags.add(self.projectHashTag_2)

        response = self.client.get("/project-hashtags/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

        self.assertEqual(
            response.json()["popularHashTags"][0]["value"],
            self.projectHashTag_2.value,
            msg="HashTag with Id {} is not the most popular hashTag but is used the most".format(
                self.projectHashTag_2_Id
            ),
        )
        self.assertEqual(
            len(response.json()["popularHashTags"]),
            3,
            msg="Number of popular hashTags !=3, but 3 hashTags have been used",
        )
