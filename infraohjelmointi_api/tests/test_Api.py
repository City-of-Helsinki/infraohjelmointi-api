import datetime
import json
from unittest.mock import patch
import uuid
from asgiref.sync import async_to_sync, sync_to_async
from django.db import connection
from django.core.management import call_command
from django.test import TestCase, AsyncClient
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from overrides import override
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from infraohjelmointi_api.models import Project, ProjectClass, ProjectDistrict, ProjectFinancial, ProjectGroup, ProjectLocation, ProjectHashTag, ProjectWiseFolder, TalpaAssetClass, TalpaProjectOpening, User
from infraohjelmointi_api.serializers import ProjectClassSerializer, ProjectDistrictSerializer, ProjectGetSerializer, ProjectGroupSerializer, ProjectLocationSerializer, ProjectHashtagSerializer
from infraohjelmointi_api.serializers.ProjectCreateSerializer import ProjectCreateSerializer
from infraohjelmointi_api.serializers.ProjectWithFinancesSerializer import ProjectWithFinancesSerializer
from infraohjelmointi_api.tests.helpers import CacheClearingMixin
from infraohjelmointi_api.views import BaseViewSet
from project.extensions.CustomTokenAuth import CustomTokenAuth


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
class ApiTestCase(CacheClearingMixin, TestCase):
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


    @patch("infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw")
    @patch.dict("os.environ", {"PW_PROJECT_FOLDER_LINK": "https://example.test/?fld={}"})
    def test_api_GET_project_detail_sync(self, mock_pw):
        setup_sync_client(self)
        Project.objects.filter(id=self.project_id).update(hkrId=123)
        ProjectWiseFolder.objects.create(hkrId=123, instanceId="folder-123")
        asset_class = TalpaAssetClass.objects.create(
            componentClass="8103000",
            account="103000",
            name="Test asset class",
            holdingPeriodYears=20,
        )
        TalpaProjectOpening.objects.create(
            project=self.project,
            subject="Uusi",
            assetClass=asset_class,
        )
        response_project = self.client.get(f"/api/projects/{self.project_id}/")

        self.assertEqual(response_project.status_code, 200)
        self.assertEqual(response_project.json()["holdingTime"], 20)
        self.assertEqual(response_project.json()["pwFolderLink"], "https://example.test/?fld=folder-123")
        mock_pw.assert_not_called()

        project_data = ProjectGetSerializer(Project.objects.get(id=self.project_id)).data
        self.assertEqual(response_project.json()["id"], project_data["id"])

    def test_api_GET_project_holding_time_is_null_when_unavailable(self):
        setup_sync_client(self)
        response_project = self.client.get(f"/api/projects/{self.project_id}/")

        self.assertEqual(response_project.status_code, 200)
        self.assertIsNone(response_project.json()["holdingTime"])

    def test_api_GET_project_holding_time_is_null_when_zero(self):
        setup_sync_client(self)
        asset_class = TalpaAssetClass.objects.create(
            componentClass="8103000",
            account="103000",
            name="Test asset class",
            holdingPeriodYears=0,
        )
        TalpaProjectOpening.objects.create(
            project=self.project,
            subject="Uusi",
            assetClass=asset_class,
        )

        response_project = self.client.get(f"/api/projects/{self.project_id}/")

        self.assertEqual(response_project.status_code, 200)
        self.assertIsNone(response_project.json()["holdingTime"])

    def test_api_project_list_holding_time_queries_do_not_grow_with_project_count(self):
        setup_sync_client(self)
        asset_class = TalpaAssetClass.objects.create(
            componentClass="8103000",
            account="103000",
            name="Test asset class",
            holdingPeriodYears=20,
        )
        TalpaProjectOpening.objects.create(
            project=self.project,
            subject="Uusi",
            assetClass=asset_class,
        )

        async def consume_stream(stream):
            return b"".join([chunk async for chunk in stream])

        def get_projects_and_talpa_query_count():
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get("/api/projects/")
                content = async_to_sync(consume_stream)(response.streaming_content)

            self.assertEqual(response.status_code, 200)
            talpa_tables = (
                TalpaProjectOpening._meta.db_table.lower(),
                TalpaAssetClass._meta.db_table.lower(),
            )
            talpa_queries = [
                query for query in queries.captured_queries
                if any(table in query["sql"].lower() for table in talpa_tables)
            ]
            return json.loads(content), len(talpa_queries)

        few_projects, few_talpa_queries = get_projects_and_talpa_query_count()
        self.assertEqual(few_projects[0]["holdingTime"], 20)

        for index in range(2, 6):
            project = Project.objects.create(
                name=f"Test project {index}",
                description="description of the test project",
                projectClass=self.project_class,
                projectDistrict=self.project_district,
                projectLocation=self.project_location,
            )
            TalpaProjectOpening.objects.create(
                project=project,
                subject="Uusi",
                assetClass=asset_class,
            )

        many_projects, many_talpa_queries = get_projects_and_talpa_query_count()

        self.assertEqual(len(many_projects), 5)
        self.assertTrue(all(project["holdingTime"] == 20 for project in many_projects))
        self.assertEqual(few_talpa_queries, 1)
        self.assertEqual(many_talpa_queries, few_talpa_queries)

    @patch("infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw")
    @patch.dict("os.environ", {"PW_PROJECT_FOLDER_LINK": "https://example.test/?fld={}"})
    def test_api_project_detail_uses_cached_folder_without_extra_queries(self, mock_pw):
        setup_sync_client(self)
        Project.objects.filter(id=self.project_id).update(hkrId=123)
        with CaptureQueriesContext(connection) as without_cache:
            empty_response = self.client.get(f"/api/projects/{self.project_id}/")
        self.assertIsNone(empty_response.json()["pwFolderLink"])

        ProjectWiseFolder.objects.create(hkrId=123, instanceId="folder-123")
        with CaptureQueriesContext(connection) as with_cache:
            response = self.client.get(f"/api/projects/{self.project_id}/")
        self.assertEqual(response.json()["pwFolderLink"], "https://example.test/?fld=folder-123")
        self.assertNotIn("pwFolderCache", response.json())
        self.assertEqual(len(with_cache), len(without_cache))
        mock_pw.assert_not_called()

        Project.objects.filter(id=self.project_id).update(hkrId=456)
        response = self.client.get(f"/api/projects/{self.project_id}/")
        self.assertIsNone(response.json()["pwFolderLink"])
        mock_pw.assert_not_called()

    @patch("infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw")
    @patch.dict("os.environ", {"PW_PROJECT_FOLDER_LINK": "https://example.test/?fld={}"})
    def test_api_project_detail_uses_refreshed_folder(self, mock_pw):
        setup_sync_client(self)
        Project.objects.filter(id=self.project_id).update(hkrId=123)
        mock_pw.return_value = {"instanceId": "folder-123"}
        call_command("refresh_pw_folder_links")
        mock_pw.reset_mock()

        response = self.client.get(f"/api/projects/{self.project_id}/")
        self.assertEqual(response.json()["pwFolderLink"], "https://example.test/?fld=folder-123")
        mock_pw.assert_not_called()

    def test_project_save_does_not_overwrite_folder_cache(self):
        Project.objects.filter(id=self.project_id).update(hkrId=123)
        project = Project.objects.get(id=self.project_id)
        ProjectWiseFolder.objects.create(hkrId=123, instanceId="folder-123")
        project.name = "Updated project"
        project.save()
        self.assertEqual(ProjectWiseFolder.objects.get(hkrId=123).instanceId, "folder-123")
        project.hkrId = 456
        project.save(update_fields=["hkrId"])
        self.assertEqual(ProjectWiseFolder.objects.get(hkrId=123).instanceId, "folder-123")

    def test_folder_cache_is_internal_to_project_serializers(self):
        for serializer_class in (ProjectGetSerializer, ProjectCreateSerializer, ProjectWithFinancesSerializer):
            with self.subTest(serializer=serializer_class.__name__):
                self.assertNotIn("pwFolderCache", serializer_class().fields)


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
class AsyncApiTestCase(CacheClearingMixin, TestCase):
    client_class = AsyncClient

    @classmethod
    def setUpTestData(cls):
        perform_shared_api_setup(cls)

    @patch("infraohjelmointi_api.services.ProjectWiseService.ProjectWiseService.get_project_from_pw")
    async def test_api_GET_streaming_projects(self, mock_pw):
        await sync_to_async(Project.objects.filter(id=ApiTestCase.project_id).update)(hkrId=123)
        await sync_to_async(ProjectWiseFolder.objects.create)(hkrId=123, instanceId="folder-123")
        token = getattr(AsyncApiTestCase, 'token', None)
        auth_header = f"Bearer {token.key}"

        asset_class = await sync_to_async(TalpaAssetClass.objects.create)(
            componentClass="8103000",
            account="103000",
            name="Test asset class",
            holdingPeriodYears=20,
        )
        await sync_to_async(TalpaProjectOpening.objects.create)(
            project=await sync_to_async(Project.objects.get)(id=ApiTestCase.project_id),
            subject="Uusi",
            assetClass=asset_class,
        )

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
        self.assertIsNone(actual_projects_list[0]["pwFolderLink"])
        self.assertIsNone(actual_projects_by_class_list[0]["pwFolderLink"])
        self.assertNotIn("pwFolderCache", actual_projects_list[0])
        mock_pw.assert_not_called()

        expected_projects_json_str = json.dumps(expected_projects_data_raw, default=str)
        comparable_expected_projects = json.loads(expected_projects_json_str)

        expected_projects_by_class_json_str = json.dumps(expected_projects_by_class_data_raw, default=str)
        comparable_expected_projects_by_class = json.loads(expected_projects_by_class_json_str)

        actual_holding_times = [project.pop("holdingTime") for project in actual_projects_list]
        actual_holding_times_by_class = [project.pop("holdingTime") for project in actual_projects_by_class_list]
        self.assertListEqual(actual_projects_list, comparable_expected_projects, msg="Data mismatch for streaming /api/projects/")
        self.assertListEqual(actual_projects_by_class_list, comparable_expected_projects_by_class, msg="Data mismatch for streaming /api/projects/?class=...")
        self.assertEqual(actual_holding_times[0], 20)
        self.assertEqual(actual_holding_times_by_class[0], 20)


def setup_sync_client(self):
    self.client = APIClient()
    self.client.credentials(HTTP_AUTHORIZATION="Bearer {}".format(self.token.key))
