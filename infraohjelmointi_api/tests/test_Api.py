from unittest.mock import patch
import uuid
from django.test import TestCase
from overrides import override
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from infraohjelmointi_api.models import Project, User
from infraohjelmointi_api.views import BaseViewSet


@patch.object(BaseViewSet, "authentication_classes", new=[])
class ApiTestCase(TestCase):
    projectId = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")

    @classmethod
    @override
    def setUpTestData(self):
        self.user = User.objects.create(
            username="AppName"
        )
        self.token = Token.objects.create(user=self.user)

        self.project = Project.objects.create(
            id=self.projectId,
            name="Test project 1",
            description="description of the test project",
        )


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
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token.key)

        response = self.client.get("/api/projects/")

        self.assertEqual(response.status_code, 200, msg="Status code != 200 when using correct token")


    def test_api_GET_all_endpoints(self):
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token.key)

        response_projects = self.client.get("/api/projects/")
        response_groups = self.client.get("/api/groups/")
        response_classes = self.client.get("/api/classes/")
        response_locations = self.client.get("/api/locations/")

        self.assertEqual(response_projects.status_code, 200, msg="Projects status code != 200")
        self.assertEqual(response_groups.status_code, 200, msg="Groups status code != 200")
        self.assertEqual(response_classes.status_code, 200, msg="Classes status code != 200")
        self.assertEqual(response_locations.status_code, 200, msg="Locations status code != 200")
