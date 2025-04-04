import datetime
import json
from unittest.mock import patch
import uuid
from django.test import TestCase
from django.urls import reverse
from infraohjelmointi_api.views.api.utils import generate_streaming_response
from overrides import override
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from infraohjelmointi_api.models import Project, ProjectClass, ProjectDistrict, ProjectFinancial, ProjectGroup, ProjectLocation, User
from infraohjelmointi_api.serializers import ProjectClassSerializer, ProjectDistrictSerializer, ProjectGetSerializer, ProjectGroupSerializer, ProjectLocationSerializer
from infraohjelmointi_api.views import BaseViewSet
from project.extensions.CustomTokenAuth import CustomTokenAuth
from django.http import StreamingHttpResponse


@patch.object(BaseViewSet, "authentication_classes", new=[])
class ApiTestCase(TestCase):
    project_district_id = uuid.UUID("a729e919-4556-4e2d-866b-dfaba470459e")
    project_id = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    project_group_id = uuid.UUID("bbba45f2-b0d4-4297-b0e2-4e60f8fa8412")
    project_financial_id = uuid.UUID("0ace4e90-4318-4282-8bb7-a0b152888642")
    master_class_id = uuid.UUID("78570e7c-58b8-4d08-a341-a6c95ad58fed")
    class_id = uuid.UUID("5f65a339-b3c9-48ee-a9b9-cb177546c241")
    class_not_found_id = uuid.UUID("5f65a339-b3c9-48ee-a9b9-cb1775461234")
    division_id = uuid.UUID("844e3102-7fb0-453b-ad7b-cf69b1644166")
    district_id = uuid.UUID("081ff330-5b0a-4ddc-b39b-cd9e53070256")

    incorrect_uuid = uuid.UUID("26ce9800-0828-4e60-80bd-150b009560ba")

    @classmethod
    @override
    def setUpTestData(cls):
        cls.user = User.objects.create(
            username="AppName"
        )
        cls.token = Token.objects.create(user=cls.user)

        cls.project_master_class = ProjectClass.objects.create(
            id=cls.master_class_id,
            name="Test Master Class",
            path="Test Master Class",
        )

        cls.project_class = cls.project_master_class.childClass.create(
            id=cls.class_id,
            name="Test Class",
            path="Test Class",
        )

        cls.project_district = ProjectDistrict.objects.create(
            id=cls.project_district_id,
            name="Test district B",
            path="Test district B",
            parent=None,
        )

        cls.district = ProjectLocation.objects.create(
            id=cls.district_id,
            name="Test district A",
            path="Test district A",
            parent=None,
        )

        cls.project_location = cls.district.childLocation.create(
            id=cls.division_id,
            name="Test division",
        )

        cls.project_group = ProjectGroup.objects.create(
            id=cls.project_group_id,
            name="Test Group",
            classRelation=cls.project_class,
            locationRelation=cls.project_location,
        )

        cls.project = Project.objects.create(
            id=cls.project_id,
            name="Test project 1",
            description="description of the test project",
            projectClass=cls.project_class,
            projectDistrict=cls.project_district,
            projectLocation=cls.project_location,
        )

        # Create financial data for the project
        year = int(datetime.date.today().year)
        for x in range(11):
            ProjectFinancial.objects.create(project=cls.project, year=str(year + x), value=str(x * 10))

        cls.queryset = Project.objects.all()
        cls.serializer_class = ProjectGetSerializer


    def test_api_custom_token_auth_init(self):
        _ = CustomTokenAuth()


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
        
        # Check token keyword is Bearer and not Token
        self.assertEqual(CustomTokenAuth.keyword, "Bearer")


    def test_api_GET_projects(self):
        self = setup_client(self)

        response_projects = self.client.get("/api/projects/")
        response_project = self.client.get("/api/projects/{}/".format(self.project_id))
        response_project_by_class = self.client.get("/api/projects/?class={}".format(self.class_id))

        self.assertEqual(response_projects.status_code, 200, msg="Projects status code != 200")
        self.assertEqual(response_project.status_code, 200, msg="Project status code != 200")
        self.assertEqual(response_project_by_class.status_code, 200, msg="Project status code != 200")

        project_data = ProjectGetSerializer(Project.objects.get(id=self.project_id)).data

        response_project_by_class_content = b"".join(response_project_by_class.streaming_content).decode('utf-8')
        response_project_by_class_json = json.loads(response_project_by_class_content)

        self.assertEqual(response_project.json()["id"], project_data["id"])
        self.assertEqual(response_project_by_class_json[0]["id"], project_data["id"])


    def test_api_GET_groups(self):
        self = setup_client(self)

        response_groups = self.client.get("/api/groups/")
        response_group = self.client.get("/api/groups/{}/".format(self.project_group_id))

        self.assertEqual(response_groups.status_code, 200, msg="Groups status code != 200")
        self.assertEqual(response_group.status_code, 200, msg="Groups status code != 200")

        group_data = ProjectGroupSerializer(ProjectGroup.objects.get(id=self.project_group_id)).data

        self.assertEqual(response_group.json()["id"], group_data["id"])


    def test_api_GET_classes(self):
        self = setup_client(self)

        response_classes = self.client.get("/api/classes/")
        response_class = self.client.get("/api/classes/{}/".format(self.class_id))
        
        self.assertEqual(response_classes.status_code, 200, msg="Classes status code != 200")
        self.assertEqual(response_class.status_code, 200, msg="Classes status code != 200")

        class_data = ProjectClassSerializer(ProjectClass.objects.get(id=self.class_id)).data

        self.assertEqual(response_class.json()["id"], class_data["id"])


    def test_api_GET_classes_with_not_existing_class_uuid(self):
        self = setup_client(self)

        response_class = self.client.get("/api/classes/{}/".format(self.class_not_found_id))
        self.assertEqual(response_class.status_code, 404)


    def test_api_GET_districts(self):
        self = setup_client(self)

        response_districts = self.client.get("/api/districts/")
        response_district = self.client.get("/api/districts/{}/".format(self.project_district_id))

        self.assertEqual(response_districts.status_code, 200, msg="Districts status code != 200")
        self.assertEqual(response_district.status_code, 200, msg="District status code != 200")

        district_data = ProjectDistrictSerializer(ProjectDistrict.objects.get(id=self.project_district_id)).data

        self.assertEqual(response_district.json()["id"], district_data["id"])


    def test_api_GET_locations(self):
        self = setup_client(self)

        response_locations = self.client.get("/api/locations/")
        response_location = self.client.get("/api/locations/{}/".format(self.division_id))

        self.assertEqual(response_locations.status_code, 200, msg="Locations status code != 200")
        self.assertEqual(response_location.status_code, 200, msg="Locations status code != 200")

        location_data = ProjectLocationSerializer(ProjectLocation.objects.get(id=self.division_id)).data

        self.assertEqual(response_location.json()["id"], location_data["id"])

    def test_retrieve_location_not_found(self):
        self = setup_client(self)
        # Test to ensure that a 404 is returned if the class does not exist
        non_existent_uuid = uuid.uuid4()
        url = reverse('apiLocations-detail', kwargs={'pk': non_existent_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


    def test_api_GET_incorrect_uuid(self):
        # Test endpoints returns 404 if object with request ID not found
        self = setup_client(self)

        self.assertEqual(self.client.get("/api/projects/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Projects status code != 404")
        self.assertEqual(self.client.get("/api/groups/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Groups status code != 404")
        self.assertEqual(self.client.get("/api/classes/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Classes status code != 404")
        self.assertEqual(self.client.get("/api/districts/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Districts status code != 404")
        self.assertEqual(self.client.get("/api/locations/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Locations status code != 404")

    def test_generate_streaming_response(self):
        self = setup_client(self)

        endpoint = "Projects"
        chunk_size = 100

        generator = generate_streaming_response(self.queryset, self.serializer_class, endpoint, chunk_size)
        result = "".join(list(generator))

        mock_http_response = StreamingHttpResponse((item.encode('utf-8') for item in result), content_type='application/json')
        actual_result = b''.join(mock_http_response.streaming_content).decode('utf-8')

        self.assertEqual(result, actual_result, msg="Generate streaming data != Project endpoint fetch")


def setup_client(self):
    self.client = APIClient()
    self.client.credentials(HTTP_AUTHORIZATION="Bearer {}".format(self.token.key))
    return self
