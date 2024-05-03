import datetime
from unittest.mock import patch
import uuid
from django.test import TestCase
from overrides import override
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from infraohjelmointi_api.models import Project, ProjectClass, ProjectFinancial, ProjectGroup, ProjectLocation, User
from infraohjelmointi_api.views import BaseViewSet


@patch.object(BaseViewSet, "authentication_classes", new=[])
class ApiTestCase(TestCase):
    projectId = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    projectGroupId = uuid.UUID("bbba45f2-b0d4-4297-b0e2-4e60f8fa8412")
    masterClassId = uuid.UUID("78570e7c-58b8-4d08-a341-a6c95ad58fed")
    classId = uuid.UUID("5f65a339-b3c9-48ee-a9b9-cb177546c241")
    divisionId = uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166")
    districtId = uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256")
    projectFinancial = uuid.UUID("0ace4e90-4318-4282-8bb7-a0b152888642")

    incorrect_uuid = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6123456")

    @classmethod
    @override
    def setUpTestData(self):
        self.user = User.objects.create(
            username="AppName"
        )
        self.token = Token.objects.create(user=self.user)

        self.projectMasterClass = ProjectClass.objects.create(
            id=self.masterClassId,
            name="Test Master Class",
            path="Test Master Class",
        )
        self.projectClass = self.projectMasterClass.childClass.create(
            name="Test Class",
            id=self.classId,
            path="Test Class",
        )
        self.district = ProjectLocation.objects.create(
            id=self.districtId,
            name="Test district",
            parent=None,
            path="Test district",
        )

        self.projectLocation = self.district.childLocation.create(
            id=self.divisionId,
            name="Test division",
        )

        self.projectGroup = ProjectGroup.objects.create(
            id=self.projectGroupId,
            name="Test Group",
            locationRelation=self.projectLocation,
            classRelation=self.projectClass,
        )

        self.project = Project.objects.create(
            id=self.projectId,
            name="Test project 1",
            description="description of the test project",
            projectClass=self.projectClass,
            projectLocation=self.projectLocation,
        )

        # Create financial data for the project
        year = int(datetime.date.today().year)
        for x in range(11):
            ProjectFinancial.objects.create(project=self.project, year=str(year + x), value=str(x * 10))


    def test_api_incorrect_token(self):
        self.client = APIClient()

        # Without token key
        response = self.client.get("/api/projects/")

        self.assertEqual(response.status_code, 401, msg="Status code != 401 when no credentials")

        # With incorrect token key
        self.client.credentials(HTTP_AUTHORIZATION="Bearer wrong-token-key")

        response = self.client.get("/api/projects/")

        self.assertEqual(response.status_code, 401, msg="Status code != 401 when using incorrect token")


    def test_api_correct_token(self):
        self = setup_client(self)

        response = self.client.get("/api/projects/")

        self.assertEqual(response.status_code, 200, msg="Status code != 200 when using correct token")


    def test_api_GET_projects(self):
        self = setup_client(self)

        response_projects = self.client.get("/api/projects/")
        response_project = self.client.get("/api/projects/{}".format(self.projectId))
        response_project_by_class = self.client.get("/api/projects/?class={}".format(self.classId))

        self.assertEqual(response_projects.status_code, 200, msg="Projects status code != 200")
        self.assertEqual(response_project.status_code, 200, msg="Project status code != 200")
        self.assertEqual(response_project_by_class.status_code, 200, msg="Project status code != 200")


    def test_api_GET_groups(self):
        self = setup_client(self)

        response_groups = self.client.get("/api/groups/")
        response_group = self.client.get("/api/groups/{}".format(self.projectGroupId))

        self.assertEqual(response_groups.status_code, 200, msg="Groups status code != 200")
        self.assertEqual(response_group.status_code, 200, msg="Groups status code != 200")


    def test_api_GET_classes(self):
        self = setup_client(self)

        response_classes = self.client.get("/api/classes/")
        response_class = self.client.get("/api/classes/{}".format(self.classId))

        self.assertEqual(response_classes.status_code, 200, msg="Classes status code != 200")
        self.assertEqual(response_class.status_code, 200, msg="Classes status code != 200")


    def test_api_GET_locations(self):
        self = setup_client(self)

        response_locations = self.client.get("/api/locations/")
        response_location = self.client.get("/api/locations/{}".format(self.divisionId))

        self.assertEqual(response_locations.status_code, 200, msg="Locations status code != 200")
        self.assertEqual(response_location.status_code, 200, msg="Locations status code != 200")


    def test_api_GET_incorrect_uuid(self):
        # Test endpoints returns 404 if object with request ID not found
        self = setup_client(self)

        self.assertEqual(self.client.get("/api/projects/{}".format(self.incorrect_uuid)).status_code, 404, msg="Projects status code != 404")
        self.assertEqual(self.client.get("/api/projects/?class={}".format(self.incorrect_uuid)).status_code, 404, msg="Projects by class status code != 404")
        self.assertEqual(self.client.get("/api/groups/{}".format(self.incorrect_uuid)).status_code, 404, msg="Groups status code != 404")
        self.assertEqual(self.client.get("/api/classes/{}".format(self.incorrect_uuid)).status_code, 404, msg="Classes status code != 404")
        self.assertEqual(self.client.get("/api/locations/{}".format(self.incorrect_uuid)).status_code, 404, msg="Locations status code != 404")


def setup_client(self):
    self.client = APIClient()
    self.client.credentials(HTTP_AUTHORIZATION="Bearer {}".format(self.token.key))
    return self
