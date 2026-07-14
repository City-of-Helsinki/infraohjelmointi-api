from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from helusers.models import ADGroup
from rest_framework import status
from rest_framework.test import APIClient

from infraohjelmointi_api.models import (
    ClassProgrammerAssignment,
    Project,
    ProjectClass,
    ProjectDistrict,
    ProjectProgramme,
    ProjectProgrammeBasicInfo,
    ProjectProgrammeDesignCriteria,
)
from infraohjelmointi_api.serializers import (
    ProjectProgrammeBasicInfoUpdateSerializer,
    ProjectProgrammeUpdateSerializer,
)
from infraohjelmointi_api.views.BaseViewSet import BaseViewSet

User = get_user_model()


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectProgrammeViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            username="project_programme_user",
            first_name="Project",
            last_name="Programme",
            email="projectprogramme@example.com",
        )

        self.project_district = ProjectDistrict.objects.create(
            name="Kallio",
            level="district",
            path="Kallio",
        )

        self.project = Project.objects.create(
            name="Test project programme project",
            description="Project used for project programme tests",
            projectDistrict=self.project_district,
        )

        self.second_project = Project.objects.create(
            name="Second project",
            description="Second project used for list tests",
            projectDistrict=self.project_district,
        )

    def _create_project_programme(self, **kwargs):
        defaults = {
            "project": self.project,
            "briefProjectProgramme": True,
            "status": "DRAFT",
        }
        defaults.update(kwargs)
        return ProjectProgramme.objects.create(**defaults)

    def test_create_project_programme(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/project-programmes/",
            {
                "project": str(self.project.id),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = ProjectProgramme.objects.get(id=response.data["id"])
        self.assertEqual(created.status, "DRAFT")
        self.assertTrue(created.briefProjectProgramme)
        self.assertEqual(created.createdBy_id, self.user.uuid)
        self.assertEqual(created.updatedBy_id, self.user.uuid)

    def test_list_and_retrieve_project_programmes(self):
        programme_1 = self._create_project_programme(project=self.project)
        programme_2 = self._create_project_programme(project=self.second_project)

        list_response = self.client.get("/project-programmes/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 2)

        retrieve_response = self.client.get(f"/project-programmes/{programme_1.id}/")
        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response.data["id"], str(programme_1.id))
        self.assertEqual(str(retrieve_response.data["project"]), str(self.project.id))

        retrieve_response_2 = self.client.get(f"/project-programmes/{programme_2.id}/")
        self.assertEqual(retrieve_response_2.status_code, status.HTTP_200_OK)
        self.assertEqual(retrieve_response_2.data["id"], str(programme_2.id))

    def test_get_by_project_returns_project_programme(self):
        programme = self._create_project_programme()

        response = self.client.get(f"/project-programmes/by-project/{self.project.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(programme.id))

    def test_get_by_project_invalid_uuid_returns_400(self):
        response = self.client.get("/project-programmes/by-project/1234/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_by_project_not_found_returns_404(self):
        response = self.client.get(f"/project-programmes/by-project/{self.project.id}/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_update_requires_draft_status(self):
        programme = self._create_project_programme(status="COMPLETE")

        response = self.client.patch(
            f"/project-programmes/{programme.id}/",
            {"briefProjectProgramme": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_switch_type_toggles_brief_project_programme(self):
        programme = self._create_project_programme(briefProjectProgramme=True)

        response = self.client.post(
            f"/project-programmes/{programme.id}/switch-type/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        programme.refresh_from_db()
        self.assertFalse(programme.briefProjectProgramme)

    def test_switch_type_rejects_extensive_to_brief_when_content_exists(self):
        programme = self._create_project_programme(briefProjectProgramme=False)
        ProjectProgrammeDesignCriteria.objects.create(
            project_programme=programme,
            status="DRAFT",
            guidingZoningRegulations="Some content",
        )

        response = self.client.post(
            f"/project-programmes/{programme.id}/switch-type/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("briefProjectProgramme", response.data)

    def test_switch_type_rejects_when_project_programme_is_complete(self):
        programme = self._create_project_programme(
            briefProjectProgramme=True,
            status="COMPLETE",
        )

        response = self.client.post(
            f"/project-programmes/{programme.id}/switch-type/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_transitions_updates_status(self):
        programme = self._create_project_programme(status="DRAFT")

        response = self.client.post(
            f"/project-programmes/{programme.id}/transitions/",
            {"to": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        programme.refresh_from_db()
        self.assertEqual(programme.status, "COMPLETE")

    def test_transitions_same_status_returns_409(self):
        programme = self._create_project_programme(status="DRAFT")

        response = self.client.post(
            f"/project-programmes/{programme.id}/transitions/",
            {"to": "DRAFT"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_transitions_invalid_target_status_returns_400(self):
        programme = self._create_project_programme(status="DRAFT")

        response = self.client.post(
            f"/project-programmes/{programme.id}/transitions/",
            {"to": "INVALID"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("to", response.data)

    def test_destroy_project_programme(self):
        programme = self._create_project_programme()

        response = self.client.delete(f"/project-programmes/{programme.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectProgramme.objects.filter(id=programme.id).exists())


class ProjectProgrammeSerializerTestCase(TestCase):
    def setUp(self):
        self.project_district = ProjectDistrict.objects.create(
            name="Pasila",
            level="district",
            path="Pasila",
        )
        self.project = Project.objects.create(
            name="Serializer project",
            description="Serializer test project",
            projectDistrict=self.project_district,
        )
        self.project_programme = ProjectProgramme.objects.create(
            project=self.project,
            status="DRAFT",
            briefProjectProgramme=True,
        )

    def test_basic_info_create_prefills_project_name_and_district(self):
        serializer = ProjectProgrammeBasicInfoUpdateSerializer(
            data={
                "project_programme": str(self.project_programme.id),
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        basic_info = serializer.save()

        self.assertEqual(basic_info.projectName, self.project.name)
        self.assertEqual(basic_info.district, self.project_district.name)

    def test_basic_info_update_serializer_requires_draft_status(self):
        basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=self.project_programme,
            status="COMPLETE",
            projectName="Existing name",
            district="Existing district",
        )

        serializer = ProjectProgrammeBasicInfoUpdateSerializer(
            basic_info,
            data={"summary": "Updated"},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("status", serializer.errors)

    def test_project_programme_update_serializer_blocks_extensive_to_brief_with_content(self):
        project_programme = ProjectProgramme.objects.create(
            project=Project.objects.create(
                name="Extensive project",
                description="Project with content",
                projectDistrict=self.project_district,
            ),
            status="DRAFT",
            briefProjectProgramme=False,
        )
        ProjectProgrammeDesignCriteria.objects.create(
            project_programme=project_programme,
            status="DRAFT",
            guidingZoningRegulations="Existing content",
        )

        serializer = ProjectProgrammeUpdateSerializer(
            project_programme,
            data={"briefProjectProgramme": True},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("briefProjectProgramme", serializer.errors)


class ProjectProgrammePermissionTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        restricted_group_name = getattr(
            settings,
            "RESTRICTED_PROGRAMMER_AD_GROUP",
            "sg_kymp_sso_io_rajoitetut_ohjelmoijat",
        )
        self.restricted_programmer_group = ADGroup.objects.create(
            name=restricted_group_name,
            display_name="Restricted Programmers",
        )

        self.allowed_user = User.objects.create_user(
            username="allowed.programmer@test.fi",
            email="allowed.programmer@test.fi",
        )
        self.allowed_user.ad_groups.add(self.restricted_programmer_group)

        self.unassigned_user = User.objects.create_user(
            username="unassigned.programmer@test.fi",
            email="unassigned.programmer@test.fi",
        )
        self.unassigned_user.ad_groups.add(self.restricted_programmer_group)

        self.district = ProjectDistrict.objects.create(
            name="Auth district",
            level="district",
            path="Auth district",
        )

        self.allowed_class = ProjectClass.objects.create(
            name="Allowed class",
            path="8 03/Allowed class",
        )
        self.unassigned_class = ProjectClass.objects.create(
            name="Unassigned class",
            path="8 03/Unassigned class",
        )

        self.allowed_project = Project.objects.create(
            name="Allowed programme project",
            description="Project in assigned class",
            projectDistrict=self.district,
            projectClass=self.allowed_class,
        )
        self.unassigned_project = Project.objects.create(
            name="Unassigned programme project",
            description="Project outside assigned class",
            projectDistrict=self.district,
            projectClass=self.unassigned_class,
        )

        self.allowed_programme = ProjectProgramme.objects.create(
            project=self.allowed_project,
            status="DRAFT",
            briefProjectProgramme=True,
        )
        self.unassigned_programme = ProjectProgramme.objects.create(
            project=self.unassigned_project,
            status="DRAFT",
            briefProjectProgramme=True,
        )

        ClassProgrammerAssignment.objects.create(
            user=self.allowed_user,
            project_class=self.allowed_class,
        )

    def test_restricted_programmer_can_retrieve_project_programme(self):
        self.client.force_authenticate(user=self.allowed_user)

        response = self.client.get(f"/project-programmes/{self.allowed_programme.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.allowed_programme.id))

    def test_restricted_programmer_can_partial_update_assigned_project_programme(self):
        self.client.force_authenticate(user=self.allowed_user)

        response = self.client.patch(
            f"/project-programmes/{self.allowed_programme.id}/",
            {"briefProjectProgramme": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.allowed_programme.refresh_from_db()
        self.assertFalse(self.allowed_programme.briefProjectProgramme)

    def test_restricted_programmer_can_switch_type_for_assigned_project_programme(self):
        self.client.force_authenticate(user=self.allowed_user)

        response = self.client.post(
            f"/project-programmes/{self.allowed_programme.id}/switch-type/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.allowed_programme.refresh_from_db()
        self.assertFalse(self.allowed_programme.briefProjectProgramme)

    def test_restricted_programmer_can_transition_assigned_project_programme_to_complete(self):
        self.client.force_authenticate(user=self.allowed_user)

        response = self.client.post(
            f"/project-programmes/{self.allowed_programme.id}/transitions/",
            {"to": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.allowed_programme.refresh_from_db()
        self.assertEqual(self.allowed_programme.status, "COMPLETE")

    def test_restricted_programmer_cannot_update_unassigned_project_programme(self):
        self.client.force_authenticate(user=self.unassigned_user)

        response = self.client.patch(
            f"/project-programmes/{self.unassigned_programme.id}/",
            {"briefProjectProgramme": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_programme_endpoint_requires_authentication(self):
        response = self.client.get(f"/project-programmes/{self.allowed_programme.id}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
