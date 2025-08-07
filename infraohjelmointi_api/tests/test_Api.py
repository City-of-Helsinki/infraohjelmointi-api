import datetime
import json
from unittest.mock import patch
import uuid
from django.test import TestCase, AsyncClient
from django.urls import reverse
from overrides import override
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from infraohjelmointi_api.models import Project, ProjectClass, ProjectDistrict, ProjectFinancial, ProjectGroup, ProjectLocation, ProjectHashTag, User
from infraohjelmointi_api.serializers import ProjectClassSerializer, ProjectDistrictSerializer, ProjectGetSerializer, ProjectGroupSerializer, ProjectLocationSerializer, ProjectHashtagSerializer
from infraohjelmointi_api.views import BaseViewSet
from project.extensions.CustomTokenAuth import CustomTokenAuth
from asgiref.sync import sync_to_async


def perform_shared_api_setup(cls):
    cls.user = User.objects.create(
            username="AppName"
        )
    cls.token = Token.objects.create(user=cls.user)

    cls.project_master_class = ProjectClass.objects.create(
        id=ApiTestCase.master_class_id,
        name="Test Master Class",
        path="Test Master Class",
    )

    cls.project_class = cls.project_master_class.childClass.create(
        id=ApiTestCase.class_id,
        name="Test Class",
        path="Test Class",
    )

    cls.project_district = ProjectDistrict.objects.create(
        id=ApiTestCase.project_district_id,
        name="Test district B",
        path="Test district B",
        parent=None,
    )

    cls.district = ProjectLocation.objects.create(
        id=ApiTestCase.district_id,
        name="Test district A",
        path="Test district A",
        parent=None,
    )

    
    cls.project_hashtag = ProjectHashTag.objects.create(
        id=ApiTestCase.project_hashtag_id,
        value="Test hashtag",
    )

    cls.project_location = cls.district.childLocation.create(
        id=ApiTestCase.division_id,
        name="Test division",
    )

    cls.project_group = ProjectGroup.objects.create(
        id=ApiTestCase.project_group_id,
        name="Test Group",
        classRelation=cls.project_class,
        locationRelation=cls.project_location,
    )

    cls.project = Project.objects.create(
        id=ApiTestCase.project_id,
        name="Test project 1",
        description="description of the test project",
        projectClass=cls.project_class,
        projectDistrict=cls.project_district,
        projectLocation=cls.project_location,
    )

    year = int(datetime.date.today().year)
    for x in range(11):
        ProjectFinancial.objects.create(project=cls.project, year=str(year + x), value=str(x * 10))


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
    project_hashtag_id = uuid.UUID("1017cb1d-5da2-4b6b-a02d-3d4fec169c70")
    incorrect_uuid = uuid.UUID("26ce9800-0828-4e60-80bd-150b009560ba")

    @classmethod
    @override
    def setUpTestData(cls):
        perform_shared_api_setup(cls)


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
        setup_sync_client(self)

        response = self.client.get("/api/projects/")

        self.assertEqual(response.status_code, 200, msg="Status code != 200 when using correct token")
        
        # Check token keyword is Bearer and not Token
        self.assertEqual(CustomTokenAuth.keyword, "Bearer")


    def test_api_GET_project_detail_sync(self):
        setup_sync_client(self)
        response_project = self.client.get(f"/api/projects/{self.project_id}/")

        self.assertEqual(response_project.status_code, 200)

        project_data = ProjectGetSerializer(Project.objects.get(id=self.project_id)).data
        self.assertEqual(response_project.json()["id"], project_data["id"])


    def test_api_GET_groups(self):
        setup_sync_client(self)

        response_groups = self.client.get("/api/groups/")
        response_group = self.client.get("/api/groups/{}/".format(self.project_group_id))

        self.assertEqual(response_groups.status_code, 200, msg="Groups status code != 200")
        self.assertEqual(response_group.status_code, 200, msg="Groups status code != 200")

        group_data = ProjectGroupSerializer(ProjectGroup.objects.get(id=self.project_group_id)).data

        self.assertEqual(response_group.json()["id"], group_data["id"])


    def test_api_GET_classes(self):
        setup_sync_client(self)

        response_classes = self.client.get("/api/classes/")
        response_class = self.client.get("/api/classes/{}/".format(self.class_id))
        
        self.assertEqual(response_classes.status_code, 200, msg="Classes status code != 200")
        self.assertEqual(response_class.status_code, 200, msg="Classes status code != 200")

        class_data = ProjectClassSerializer(ProjectClass.objects.get(id=self.class_id)).data

        self.assertEqual(response_class.json()["id"], class_data["id"])


    def test_api_GET_classes_with_not_existing_class_uuid(self):
        setup_sync_client(self)

        response_class = self.client.get("/api/classes/{}/".format(self.class_not_found_id))
        self.assertEqual(response_class.status_code, 404)


    def test_api_GET_districts(self):
        setup_sync_client(self)

        response_districts = self.client.get("/api/districts/")
        response_district = self.client.get("/api/districts/{}/".format(self.project_district_id))

        self.assertEqual(response_districts.status_code, 200, msg="Districts status code != 200")
        self.assertEqual(response_district.status_code, 200, msg="District status code != 200")

        district_data = ProjectDistrictSerializer(ProjectDistrict.objects.get(id=self.project_district_id)).data

        self.assertEqual(response_district.json()["id"], district_data["id"])


    def test_api_GET_hashtags(self):
        setup_sync_client(self)

        response_hashtags = self.client.get("/api/hashtags/")
        response_hashtag = self.client.get("/api/hashtags/{}/".format(self.project_hashtag_id))

        self.assertEqual(response_hashtags.status_code, 200, msg="Hashtags status code != 200")
        self.assertEqual(response_hashtag.status_code, 200, msg="Hashtag status code != 200")

        hashtag_data = ProjectHashtagSerializer(ProjectHashTag.objects.get(id=self.project_hashtag_id)).data

        self.assertEqual(response_hashtag.json()["id"], hashtag_data["id"])


    def test_api_GET_locations(self):
        setup_sync_client(self)

        response_locations = self.client.get("/api/locations/")
        response_location = self.client.get("/api/locations/{}/".format(self.division_id))

        self.assertEqual(response_locations.status_code, 200, msg="Locations status code != 200")
        self.assertEqual(response_location.status_code, 200, msg="Locations status code != 200")

        location_data = ProjectLocationSerializer(ProjectLocation.objects.get(id=self.division_id)).data

        self.assertEqual(response_location.json()["id"], location_data["id"])

    def test_retrieve_location_not_found(self):
        # Test to ensure that a 404 is returned if the class does not exist
        setup_sync_client(self)
        non_existent_uuid = uuid.uuid4()
        url = reverse('apiLocations-detail', kwargs={'pk': non_existent_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


    def test_api_GET_incorrect_uuid(self):
        # Test endpoints returns 404 if object with request ID not found
        setup_sync_client(self)

        self.assertEqual(self.client.get("/api/projects/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Projects status code != 404")
        self.assertEqual(self.client.get("/api/groups/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Groups status code != 404")
        self.assertEqual(self.client.get("/api/classes/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Classes status code != 404")
        self.assertEqual(self.client.get("/api/districts/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Districts status code != 404")
        self.assertEqual(self.client.get("/api/locations/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Locations status code != 404")
        self.assertEqual(self.client.get("/api/hashtags/{}/".format(self.incorrect_uuid)).status_code, 404, msg="Hashtags status code != 404")


@patch.object(BaseViewSet, "authentication_classes", new=[])
class AsyncApiTestCase(TestCase):
    client_class = AsyncClient

    @classmethod
    def setUpTestData(cls):
        perform_shared_api_setup(cls)

    async def test_api_GET_streaming_projects(self):
        token = getattr(AsyncApiTestCase, 'token', None)
        auth_header = f"Bearer {token.key}"

        projects_url = "/api/projects/"
        projects_by_class_url = f"/api/projects/?class={ApiTestCase.class_id}"

        response_projects = await self.client.get(projects_url, AUTHORIZATION=auth_header)
        response_projects_by_class = await self.client.get(projects_by_class_url, AUTHORIZATION=auth_header)

        self.assertEqual(response_projects.status_code, 200, msg="Streaming Projects status code != 200")
        self.assertEqual(response_projects_by_class.status_code, 200, msg="Streaming Projects by class status code != 200")

        all_projects_qs = Project.objects.all()
        expected_projects_data_raw = await sync_to_async(
            lambda: ProjectGetSerializer(all_projects_qs, many=True).data
        )()

        filtered_projects_qs = Project.objects.filter(projectClass=ApiTestCase.class_id)
        expected_projects_by_class_data_raw = await sync_to_async(
            lambda: ProjectGetSerializer(filtered_projects_qs, many=True).data
        )()

        streamed_chunks_all = []
        async for chunk in response_projects.streaming_content:
            streamed_chunks_all.append(chunk)

        streamed_content_str_all = b"".join(streamed_chunks_all).decode('utf-8')
        actual_projects_list = json.loads(streamed_content_str_all)

        streamed_chunks_class = []
        async for chunk in response_projects_by_class.streaming_content:
            streamed_chunks_class.append(chunk)

        streamed_content_str_class = b"".join(streamed_chunks_class).decode('utf-8')
        actual_projects_by_class_list = json.loads(streamed_content_str_class)

        expected_projects_json_str = json.dumps(expected_projects_data_raw, default=str)
        comparable_expected_projects = json.loads(expected_projects_json_str)

        expected_projects_by_class_json_str = json.dumps(expected_projects_by_class_data_raw, default=str)
        comparable_expected_projects_by_class = json.loads(expected_projects_by_class_json_str)

        self.assertListEqual(actual_projects_list, comparable_expected_projects, msg="Data mismatch for streaming /api/projects/")
        self.assertListEqual(actual_projects_by_class_list, comparable_expected_projects_by_class, msg="Data mismatch for streaming /api/projects/?class=...")


def setup_sync_client(self):
    self.client = APIClient()
    self.client.credentials(HTTP_AUTHORIZATION="Bearer {}".format(self.token.key))
