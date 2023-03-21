from django.test import TestCase
from rest_framework.renderers import JSONRenderer
from infraohjelmointi_api.models import (
    ProjectGroup,
    ProjectLocation,
    ProjectClass,
    Project,
)
from infraohjelmointi_api.serializers import ProjectGroupSerializer
import uuid
from overrides import override


class projectGroupTestCase(TestCase):
    projectGroup_1_Id = uuid.UUID("bbba45f2-b0d4-4297-b0e2-4e60f8fa8412")
    projectGroup_2_Id = uuid.UUID("bee657d4-a2cc-4c04-a75b-edc12275dd62")
    projectGroup_3_Id = uuid.UUID("b2e2808c-831b-4db2-b0a8-f6c6d270af1a")
    projectClassId = uuid.UUID("5f65a339-b3c9-48ee-a9b9-cb177546c241")
    projectMasterClassId = uuid.UUID("78570e7c-58b8-4d08-a341-a6c95ad58fed")
    projectMainDistrictId = uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256")
    projectLocationId = uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166")
    projectId = uuid.UUID("33814e76-7bdc-47c2-bf08-7ed43a96e042")

    @classmethod
    @override
    def setUpTestData(self):
        self.projectMasterClass = ProjectClass.objects.create(
            id=self.projectMasterClassId, name="Test Master Class", parent=None
        )
        self.projectClass = self.projectMasterClass.childClass.create(
            name="Test Class", id=self.projectClassId
        )
        self.mainDistrict = ProjectLocation.objects.create(
            id=self.projectMainDistrictId,
            name="Test main districtRelation",
            parent=None,
        )
        self.projectLocation = self.mainDistrict.childLocation.create(
            id=self.projectLocationId, name="Test districtRelation"
        )

        self.project = Project.objects.create(
            id=self.projectId,
            name="Test project 1",
            description="description of the test project",
        )
        self.projectGroup = ProjectGroup.objects.create(
            id=self.projectGroup_1_Id,
            name="Test Group",
            districtRelation=self.projectLocation,
            classRelation=self.projectClass,
        )

    def test_ProjectGroup_is_created(self):

        self.assertEqual(
            ProjectGroup.objects.filter(id=self.projectGroup_1_Id).exists(),
            True,
            msg="Created ProjectGroup with Id {} does not exist in DB".format(
                self.projectGroup_1_Id
            ),
        )
        projectGroup = ProjectGroup.objects.get(id=self.projectGroup_1_Id)
        self.assertIsInstance(
            projectGroup,
            ProjectGroup,
            msg="Object retrieved from DB != typeof projectGroup",
        )
        self.assertEqual(
            projectGroup.id,
            self.projectGroup.id,
            msg="Object from DB != created Object",
        )

    def test_GET_all_ProjectGroups(self):
        response = self.client.get("/project-groups/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(
            len(response.json()), 1, msg="Number of returned projectGroups != 1"
        )
        self.projectGroup = ProjectGroup.objects.create(
            id=self.projectGroup_2_Id,
            name="Test Group 2",
        )
        response = self.client.get("/project-groups/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(
            len(response.json()), 2, msg="Number of returned projectGroups != 2"
        )

    def test_GET_one_ProjectGroup(self):
        response = self.client.get("/project-groups/{}/".format(self.projectGroup_1_Id))
        self.assertEqual(
            response.json()["name"],
            self.projectGroup.name,
            msg="Response doesn't match the object in DB",
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        # serialize the model instances
        serializer = ProjectGroupSerializer(
            ProjectGroup.objects.get(id=self.projectGroup_1_Id), many=False
        )

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected

        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(response.content, result_expected)

    def test_POST_ProjectGroup(self):
        data = {
            "name": "POST Group",
            "classRelation": None,
            "districtRelation": None,
        }
        response = self.client.post(
            "/project-groups/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201, msg="Status code != 201")
        new_createdId = response.json()["id"]
        self.assertEqual(
            ProjectGroup.objects.filter(id=new_createdId).exists(),
            True,
            msg="projectGroup created using POST request does not exist in DB",
        )

    def test_POST_ProjectGroup_with_Project(self):
        data = {
            "name": "POST Group with project",
            "classRelation": None,
            "districtRelation": None,
            "projects": [self.projectId],
        }
        response = self.client.post(
            "/project-groups/", data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201, msg="Status code != 201")
        new_createdId = response.json()["id"]
        self.assertEqual(
            ProjectGroup.objects.filter(id=new_createdId).exists(),
            True,
            msg="projectGroup created using POST request does not exist in DB",
        )

        self.assertEqual(
            Project.objects.get(id=self.projectId).projectGroup,
            ProjectGroup.objects.get(id=new_createdId),
            msg="Newly created ProjectGroup not assignd to Project",
        )
        response = self.client.post(
            "/project-groups/", data, content_type="application/json"
        )
        self.assertEqual(
            response.status_code,
            400,
            msg="Status code != 400",
        )
        errorMessage = response.json()["errors"][0]["detail"]
        self.assertEqual(
            errorMessage,
            "Project: {} with id: {} already belongs to the group: {} with id: {}".format(
                self.project.name,
                self.projectId,
                Project.objects.get(id=self.projectId).projectGroup.name,
                Project.objects.get(id=self.projectId).projectGroup_id,
            ),
            msg="Project which already belongs to a group should not be assigned to another group",
        )
        data["projects"] = ["6e3993ab-f15d-4acf-b151-8dd641098a26"]
        response = self.client.post(
            "/project-groups/", data, content_type="application/json"
        )
        self.assertEqual(
            response.status_code,
            404,
            msg="Status code != 404",
        )
        errorMessage = response.json()["errors"][0]["detail"]
        self.assertEqual(
            errorMessage,
            "Not found.",
            msg="Should throw error if project is not found in DB",
        )

    def test_PATCH_projectGroup(self):
        data = {
            "name": "PATCH test",
        }
        response = self.client.patch(
            "/project-groups/{}/".format(self.projectGroup_1_Id),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["name"],
            data["name"],
            msg="Data not updated in the DB",
        )

    def test_DELETE_projectGroup(self):
        response = self.client.delete(
            "/project-groups/{}/".format(self.projectGroup_1_Id)
        )
        self.assertEqual(
            response.status_code,
            204,
            msg="Error deleting projectGroup with Id {}".format(self.projectGroup_1_Id),
        )
        self.assertEqual(
            ProjectGroup.objects.filter(id=self.projectGroup_1_Id).exists(),
            False,
            msg="projectGroup with Id {} still exists in DB".format(
                self.projectGroup_1_Id
            ),
        )
