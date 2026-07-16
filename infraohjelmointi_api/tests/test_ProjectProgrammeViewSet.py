import uuid
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from helusers.models import ADGroup
from rest_framework import status
from rest_framework.test import APIClient

from infraohjelmointi_api.models import (
    ClassProgrammerAssignment,
    Person,
    Project,
    ProjectClass,
    ProjectDistrict,
    ProjectProgramme,
    ProjectProgrammeBasicInfo,
    ProjectProgrammeDesignCriteria,
    ProjectProgrammeLink,
    ProjectProgrammeOtherAttachments,
)
from infraohjelmointi_api.serializers import (
    ProjectProgrammeBasicInfoGetSerializer,
    ProjectProgrammeBasicInfoUpdateSerializer,
    ProjectProgrammeLinkUpdateSerializer,
    ProjectProgrammeUpdateSerializer,
)
from infraohjelmointi_api.permissions import get_project_programme_contributor_group_name
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
        self.client.force_authenticate(user=self.user)

        self.responsible_person = Person.objects.create(
            firstName="Project",
            lastName="Programme",
            email=self.user.email,
            title="Planner",
            phone="1234567",
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
            personPlanning=self.responsible_person,
        )

        self.second_project = Project.objects.create(
            name="Second project",
            description="Second project used for list tests",
            projectDistrict=self.project_district,
            personPlanning=self.responsible_person,
        )

    def _create_project_programme(self, **kwargs):
        defaults = {
            "project": self.project,
            "briefProjectProgramme": True,
            "status": "DRAFT",
        }
        defaults.update(kwargs)
        return ProjectProgramme.objects.create(**defaults)

    def _basic_info_payload(self):
        return {
            "projectProgrammeCompiler": "Compiler",
            "personsInvolved": "Person",
            "inspector": "Inspector",
            "estimatedCosts": "100000",
        }

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

    def test_get_by_project_accepts_uppercase_uuid(self):
        programme = self._create_project_programme()

        uppercase_project_id = str(self.project.id).upper()
        response = self.client.get(f"/project-programmes/by-project/{uppercase_project_id}/")

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

    def test_partial_update_cannot_change_project(self):
        programme = self._create_project_programme(project=self.project)

        response = self.client.patch(
            f"/project-programmes/{programme.id}/",
            {"project": str(self.second_project.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project", response.data)
        programme.refresh_from_db()
        self.assertEqual(programme.project_id, self.project.id)

    def test_partial_update_cannot_change_status(self):
        programme = self._create_project_programme(status="DRAFT")

        response = self.client.patch(
            f"/project-programmes/{programme.id}/",
            {"status": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        programme.refresh_from_db()
        self.assertEqual(programme.status, "DRAFT")

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

    def test_transitions_to_complete_updates_draft_sections_to_complete(self):
        programme = self._create_project_programme(status="DRAFT")
        basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="DRAFT",
            projectName="Test name",
            district="Test district",
        )
        design_criteria = ProjectProgrammeDesignCriteria.objects.create(
            project_programme=programme,
            status="COMPLETE",
            guidingZoningRegulations="Existing",
        )

        response = self.client.post(
            f"/project-programmes/{programme.id}/transitions/",
            {"to": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        programme.refresh_from_db()
        basic_info.refresh_from_db()
        design_criteria.refresh_from_db()
        self.assertEqual(programme.status, "COMPLETE")
        self.assertEqual(basic_info.status, "COMPLETE")
        self.assertEqual(design_criteria.status, "COMPLETE")

    def test_section_transitions_updates_status(self):
        programme = self._create_project_programme(status="DRAFT")
        basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="DRAFT",
            projectName="Test name",
            district="Test district",
        )

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/basic-info/transitions/",
            {"to": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        basic_info.refresh_from_db()
        self.assertEqual(basic_info.status, "COMPLETE")
        self.assertEqual(response.data["section"], "basicInfo")

    def test_section_transitions_same_status_returns_409(self):
        programme = self._create_project_programme(status="DRAFT")
        ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="DRAFT",
            projectName="Test name",
            district="Test district",
        )

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/basic-info/transitions/",
            {"to": "DRAFT"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_section_transitions_unknown_section_key_returns_404(self):
        programme = self._create_project_programme(status="DRAFT")

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/unknown/transitions/",
            {"to": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_section_transitions_missing_section_returns_404(self):
        programme = self._create_project_programme(status="DRAFT")

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/basic-info/transitions/",
            {"to": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_section_transitions_rejects_when_parent_programme_is_complete(self):
        programme = self._create_project_programme(status="COMPLETE")
        ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="COMPLETE",
            projectName="Test name",
            district="Test district",
        )

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/basic-info/transitions/",
            {"to": "DRAFT"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "Sections can only be transitioned when the project programme is in DRAFT status.",
        )

    def test_destroy_project_programme(self):
        programme = self._create_project_programme()

        response = self.client.delete(f"/project-programmes/{programme.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectProgramme.objects.filter(id=programme.id).exists())

    def test_destroy_complete_project_programme_returns_409(self):
        programme = self._create_project_programme(status="COMPLETE")

        response = self.client.delete(f"/project-programmes/{programme.id}/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "Only project programmes in DRAFT status can be deleted.",
        )
        self.assertTrue(ProjectProgramme.objects.filter(id=programme.id).exists())

    def test_post_section_basic_info_creates_section(self):
        programme = self._create_project_programme()

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            {"summary": "A summary"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["project_programme"]), str(programme.id))
        self.assertEqual(response.data["projectName"], self.project.name)
        self.assertEqual(response.data["summary"], "A summary")
        self.assertEqual(response.data["estimatedCosts"], "")

    def test_post_section_basic_info_sets_created_by(self):
        self.client.force_authenticate(user=self.user)
        programme = self._create_project_programme()

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            self._basic_info_payload(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        basic_info = ProjectProgrammeBasicInfo.objects.get(project_programme=programme)
        self.assertEqual(basic_info.createdBy_id, self.user.uuid)
        self.assertEqual(basic_info.updatedBy_id, self.user.uuid)

    def test_post_section_basic_info_returns_409_if_already_exists(self):
        programme = self._create_project_programme()
        ProjectProgrammeBasicInfo.objects.create(project_programme=programme, status="DRAFT")

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_patch_section_basic_info_updates_section(self):
        programme = self._create_project_programme()
        ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="DRAFT",
            projectName=self.project.name,
            district=self.project_district.name,
            summary="Original",
        )

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            {**self._basic_info_payload(), "summary": "Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"], "Updated")

    def test_patch_section_basic_info_requires_brief_programme_fields(self):
        programme = self._create_project_programme()
        ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="DRAFT",
        )

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            {"summary": "Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("projectProgrammeCompiler", response.data)
        self.assertIn("personsInvolved", response.data)
        self.assertIn("inspector", response.data)
        self.assertIn("estimatedCosts", response.data)

    def test_patch_section_basic_info_succeeds_with_partial_payload_when_required_fields_already_saved(self):
        programme = self._create_project_programme()
        ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="DRAFT",
            projectName=self.project.name,
            district=self.project_district.name,
            **self._basic_info_payload(),
        )

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            {"summary": "Only summary changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["summary"], "Only summary changed")
        self.assertEqual(response.data["projectProgrammeCompiler"], "Compiler")

    def test_patch_section_basic_info_returns_404_if_not_exists(self):
        programme = self._create_project_programme()

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            {"summary": "Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_section_basic_info_blocked_when_section_is_complete(self):
        programme = self._create_project_programme()
        ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="COMPLETE",
            projectName="Existing",
            district="Existing",
        )

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            {**self._basic_info_payload(), "summary": "Blocked update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_section_mutation_blocked_when_parent_programme_is_complete(self):
        programme = self._create_project_programme(status="COMPLETE")

        post_response = self.client.post(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            {"summary": "Blocked create"},
            format="json",
        )

        self.assertEqual(post_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            post_response.data["detail"],
            "Only sections of project programmes in DRAFT status can be edited.",
        )
        self.assertFalse(
            ProjectProgrammeBasicInfo.objects.filter(project_programme=programme).exists()
        )

        programme.status = "DRAFT"
        programme.save(update_fields=["status"])
        ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="DRAFT",
            summary="Original",
        )
        programme.status = "COMPLETE"
        programme.save(update_fields=["status"])

        patch_response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            {"summary": "Blocked update"},
            format="json",
        )

        self.assertEqual(patch_response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            patch_response.data["detail"],
            "Only sections of project programmes in DRAFT status can be edited.",
        )
        self.assertEqual(
            ProjectProgrammeBasicInfo.objects.get(project_programme=programme).summary,
            "Original",
        )

    def test_patch_section_basic_info_cannot_change_parent_programme(self):
        programme = self._create_project_programme(project=self.project)
        second_programme = self._create_project_programme(project=self.second_project)
        section = ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="DRAFT",
            summary="Original",
        )

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/basic-info/",
            {"project_programme": str(second_programme.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        section.refresh_from_db()
        self.assertEqual(section.project_programme_id, programme.id)

    def test_patch_section_design_criteria_cannot_change_parent_programme(self):
        programme = self._create_project_programme(project=self.project, briefProjectProgramme=False)
        second_programme = self._create_project_programme(
            project=self.second_project,
            briefProjectProgramme=False,
        )
        section = ProjectProgrammeDesignCriteria.objects.create(
            project_programme=programme,
            status="DRAFT",
            guidingZoningRegulations="Original",
        )

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/design-criteria/",
            {"project_programme": str(second_programme.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        section.refresh_from_db()
        self.assertEqual(section.project_programme_id, programme.id)

    def test_patch_section_other_attachments_cannot_change_parent_programme(self):
        programme = self._create_project_programme(project=self.project, briefProjectProgramme=False)
        second_programme = self._create_project_programme(
            project=self.second_project,
            briefProjectProgramme=False,
        )
        section = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=programme,
            status="DRAFT",
        )

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/other-attachments/",
            {"project_programme": str(second_programme.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        section.refresh_from_db()
        self.assertEqual(section.project_programme_id, programme.id)

    def test_post_section_design_criteria_creates_section(self):
        programme = self._create_project_programme(briefProjectProgramme=False)

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/design-criteria/",
            {"guidingZoningRegulations": "Some text"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["project_programme"]), str(programme.id))

    def test_post_section_traffic_planning_criteria_creates_section(self):
        programme = self._create_project_programme(briefProjectProgramme=False)

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/traffic-planning-criteria/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["project_programme"]), str(programme.id))

    def test_post_section_urban_spacing_planning_criteria_creates_section(self):
        programme = self._create_project_programme(briefProjectProgramme=False)

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/urban-spacing-planning-criteria/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["project_programme"]), str(programme.id))

    def test_post_section_maintenance_needs_creates_section(self):
        programme = self._create_project_programme(briefProjectProgramme=False)

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/maintenance-needs/",
            {"maintenanceNeeds": "Some needs"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["project_programme"]), str(programme.id))

    def test_post_section_interaction_and_related_projects_creates_section(self):
        programme = self._create_project_programme(briefProjectProgramme=False)

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/interaction-and-related-projects/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["project_programme"]), str(programme.id))

    def test_post_section_other_attachments_creates_section(self):
        programme = self._create_project_programme(briefProjectProgramme=False)

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/other-attachments/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["project_programme"]), str(programme.id))

    def test_post_link_creates_link(self):
        programme = self._create_project_programme()
        other_attachments = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=programme, status="DRAFT"
        )
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/links/",
            {
                "contentType": content_type.id,
                "objectId": str(other_attachments.id),
                "value": "https://example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["value"], "https://example.com")
        self.assertTrue(ProjectProgrammeLink.objects.filter(id=response.data["id"]).exists())

    def test_post_link_rejects_section_from_different_programme(self):
        programme = self._create_project_programme(project=self.project)
        second_programme = self._create_project_programme(project=self.second_project)
        other_attachments = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=second_programme,
            status="DRAFT",
        )
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/links/",
            {
                "contentType": content_type.id,
                "objectId": str(other_attachments.id),
                "value": "https://example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(ProjectProgrammeLink.objects.filter(objectId=other_attachments.id).exists())

    def test_post_link_rejects_non_programme_section_content_type(self):
        programme = self._create_project_programme(project=self.project)
        non_section_content_type = ContentType.objects.get_for_model(Project)

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/links/",
            {
                "contentType": non_section_content_type.id,
                "objectId": str(self.project.id),
                "value": "https://example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(ProjectProgrammeLink.objects.exists())

    def test_patch_link_updates_link(self):
        programme = self._create_project_programme()
        other_attachments = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=programme, status="DRAFT"
        )
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)
        link = ProjectProgrammeLink.objects.create(
            contentType=content_type,
            objectId=other_attachments.id,
            value="https://original.com",
        )

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/links/{link.id}/",
            {"value": "https://updated.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["value"], "https://updated.com")

    def test_delete_link_removes_link(self):
        programme = self._create_project_programme()
        other_attachments = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=programme, status="DRAFT"
        )
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)
        link = ProjectProgrammeLink.objects.create(
            contentType=content_type,
            objectId=other_attachments.id,
            value="https://example.com",
        )

        response = self.client.delete(
            f"/project-programmes/{programme.id}/sections/links/{link.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectProgrammeLink.objects.filter(id=link.id).exists())

    def test_patch_link_rejects_link_from_different_programme(self):
        programme = self._create_project_programme(project=self.project)
        second_programme = self._create_project_programme(project=self.second_project)
        other_attachments = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=second_programme,
            status="DRAFT",
        )
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)
        link = ProjectProgrammeLink.objects.create(
            contentType=content_type,
            objectId=other_attachments.id,
            value="https://original.com",
        )

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/links/{link.id}/",
            {"value": "https://updated.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        link.refresh_from_db()
        self.assertEqual(link.value, "https://original.com")

    def test_patch_link_cannot_change_target(self):
        programme = self._create_project_programme(project=self.project)
        other_attachments = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=programme,
            status="DRAFT",
        )
        second_programme = self._create_project_programme(project=self.second_project)
        another_attachments = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=second_programme,
            status="DRAFT",
        )
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)
        link = ProjectProgrammeLink.objects.create(
            contentType=content_type,
            objectId=other_attachments.id,
            value="https://original.com",
        )

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/links/{link.id}/",
            {"objectId": str(another_attachments.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        link.refresh_from_db()
        self.assertEqual(link.objectId, other_attachments.id)

    def test_delete_link_rejects_link_from_different_programme(self):
        programme = self._create_project_programme(project=self.project)
        second_programme = self._create_project_programme(project=self.second_project)
        other_attachments = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=second_programme,
            status="DRAFT",
        )
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)
        link = ProjectProgrammeLink.objects.create(
            contentType=content_type,
            objectId=other_attachments.id,
            value="https://example.com",
        )

        response = self.client.delete(
            f"/project-programmes/{programme.id}/sections/links/{link.id}/",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(ProjectProgrammeLink.objects.filter(id=link.id).exists())

    def test_patch_nonexistent_link_returns_404(self):
        programme = self._create_project_programme()

        response = self.client.patch(
            f"/project-programmes/{programme.id}/sections/links/{uuid.uuid4()}/",
            {"value": "https://example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_link_on_locked_section_returns_400(self):
        """Regression: link serializer must check section_instance.is_locked, not the undefined `instance`."""
        programme = self._create_project_programme()
        other_attachments = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=programme, status="COMPLETE"
        )
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)

        response = self.client.post(
            f"/project-programmes/{programme.id}/sections/links/",
            {
                "contentType": content_type.id,
                "objectId": str(other_attachments.id),
                "value": "https://example.com",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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

    def _basic_info_payload(self):
        return {
            "projectProgrammeCompiler": "Compiler",
            "personsInvolved": "Person",
            "inspector": "Inspector",
            "estimatedCosts": "100000",
        }

    def test_basic_info_create_prefills_project_name_and_district(self):
        serializer = ProjectProgrammeBasicInfoUpdateSerializer(
            data={
                "project_programme": str(self.project_programme.id),
                **self._basic_info_payload(),
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        basic_info = serializer.save()

        self.assertEqual(basic_info.projectName, self.project.name)
        self.assertEqual(basic_info.district, self.project_district.name)

    def test_basic_info_create_allows_incomplete_brief_fields(self):
        serializer = ProjectProgrammeBasicInfoUpdateSerializer(
            data={
                "project_programme": str(self.project_programme.id),
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertFalse(serializer.fields["projectProgrammeCompiler"].required)
        self.assertFalse(serializer.fields["personsInvolved"].required)
        self.assertFalse(serializer.fields["inspector"].required)
        self.assertFalse(serializer.fields["estimatedCosts"].required)

    def test_basic_info_partial_update_requires_missing_field_when_never_saved(self):
        basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=self.project_programme,
            status="DRAFT",
            projectName=self.project.name,
            district=self.project_district.name,
        )

        serializer = ProjectProgrammeBasicInfoUpdateSerializer(
            basic_info,
            data={"projectProgrammeCompiler": "Compiler"},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("personsInvolved", serializer.errors)
        self.assertIn("inspector", serializer.errors)
        self.assertIn("estimatedCosts", serializer.errors)
        self.assertNotIn("projectProgrammeCompiler", serializer.errors)

    def test_basic_info_partial_update_allows_omitting_previously_saved_required_fields(self):
        basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=self.project_programme,
            status="DRAFT",
            projectName=self.project.name,
            district=self.project_district.name,
            **self._basic_info_payload(),
        )

        serializer = ProjectProgrammeBasicInfoUpdateSerializer(
            basic_info,
            data={"projectProgrammeCompiler": "Updated compiler"},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.projectProgrammeCompiler, "Updated compiler")
        self.assertEqual(updated.personsInvolved, "Person")

    def test_basic_info_complete_fields_are_required_and_brief_field_hidden(self):
        programme = ProjectProgramme.objects.create(
            project=Project.objects.create(
                name="Complete serializer project",
                description="Complete serializer test project",
                projectDistrict=self.project_district,
            ),
            status="DRAFT",
            briefProjectProgramme=False,
        )
        basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            status="DRAFT",
        )
        serializer = ProjectProgrammeBasicInfoUpdateSerializer(
            basic_info,
            data={},
            partial=False,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("summary", serializer.errors)
        self.assertIn("strategyGoals", serializer.errors)
        self.assertNotIn("estimatedCosts", serializer.fields)
        self.assertFalse(serializer.fields["inspector"].required)
        self.assertFalse(serializer.fields["specialConsiderations"].required)

        get_serializer = ProjectProgrammeBasicInfoGetSerializer(basic_info)
        self.assertNotIn("estimatedCosts", get_serializer.fields)
        self.assertIn("specialConsiderations", get_serializer.fields)

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

    def test_project_programme_update_serializer_rejects_project_change(self):
        other_project = Project.objects.create(
            name="Other serializer project",
            description="Other serializer test project",
            projectDistrict=self.project_district,
        )

        serializer = ProjectProgrammeUpdateSerializer(
            self.project_programme,
            data={"project": str(other_project.id)},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("project", serializer.errors)

    def test_link_update_serializer_blocks_locked_section(self):
        other_attachments = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=self.project_programme, status="COMPLETE"
        )
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)

        serializer = ProjectProgrammeLinkUpdateSerializer(
            data={
                "contentType": content_type.id,
                "objectId": str(other_attachments.id),
                "value": "https://example.com",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("detail", serializer.errors)

    def test_link_update_serializer_cannot_change_target(self):
        attachments_1 = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=self.project_programme,
            status="DRAFT",
        )
        other_programme = ProjectProgramme.objects.create(
            project=Project.objects.create(
                name="Another serializer project",
                description="Another serializer test project",
                projectDistrict=self.project_district,
            ),
            status="DRAFT",
            briefProjectProgramme=True,
        )
        attachments_2 = ProjectProgrammeOtherAttachments.objects.create(
            project_programme=other_programme,
            status="DRAFT",
        )
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)
        link = ProjectProgrammeLink.objects.create(
            contentType=content_type,
            objectId=attachments_1.id,
            value="https://example.com",
        )

        serializer = ProjectProgrammeLinkUpdateSerializer(
            link,
            data={"objectId": str(attachments_2.id)},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("detail", serializer.errors)


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
        self.viewer_group = ADGroup.objects.create(
            name="sg_kymp_sso_io_katselijat_muut",
            display_name="Viewers",
        )
        self.project_manager_group = ADGroup.objects.create(
            name="sg_kymp_sso_io_projektipaallikot",
            display_name="Project managers",
        )
        self.project_programme_contributor_group = ADGroup.objects.create(
            name=get_project_programme_contributor_group_name(),
            display_name="Project programme contributors",
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

        self.project_manager_user = User.objects.create_user(
            username="project.manager@test.fi",
            email="project.manager@test.fi",
        )
        self.project_manager_user.ad_groups.add(self.project_manager_group)

        self.responsible_viewer_user = User.objects.create_user(
            username="responsible.viewer@test.fi",
            email="responsible.viewer@test.fi",
        )
        self.responsible_viewer_user.ad_groups.add(self.viewer_group)

        self.contributor_user = User.objects.create_user(
            username="contributor.user@test.fi",
            email="contributor.user@test.fi",
        )
        self.contributor_user.ad_groups.add(self.project_programme_contributor_group)

        self.responsible_person = Person.objects.create(
            firstName="Responsible",
            lastName="Viewer",
            email="responsible.viewer@test.fi",
            title="Landscape architect",
            phone="0401234567",
        )
        self.responsible_programmer_person = Person.objects.create(
            firstName="Allowed",
            lastName="Programmer",
            email="allowed.programmer@test.fi",
            title="Programmer",
            phone="0402345678",
        )
        self.responsible_programmer = ProjectProgrammer.objects.create(
            firstName="Allowed",
            lastName="Programmer",
            person=self.responsible_programmer_person,
        )

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
            personPlanning=self.responsible_person,
            personProgramming=self.responsible_programmer,
        )
        self.unassigned_project = Project.objects.create(
            name="Unassigned programme project",
            description="Project outside assigned class",
            projectDistrict=self.district,
            projectClass=self.unassigned_class,
        )
        self.responsible_project = Project.objects.create(
            name="Responsible project",
            description="Project for responsible creator",
            projectDistrict=self.district,
            personPlanning=self.responsible_person,
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

    def test_restricted_programmer_cannot_reassign_assigned_programme_to_unassigned_project(self):
        self.client.force_authenticate(user=self.allowed_user)

        response = self.client.patch(
            f"/project-programmes/{self.allowed_programme.id}/",
            {"project": str(self.unassigned_project.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project", response.data)
        self.allowed_programme.refresh_from_db()
        self.assertEqual(self.allowed_programme.project_id, self.allowed_project.id)

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

    def test_restricted_programmer_can_transition_assigned_section_to_complete(self):
        self.client.force_authenticate(user=self.allowed_user)
        basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=self.allowed_programme,
            status="DRAFT",
            projectName="Allowed",
            district="District",
        )

        response = self.client.post(
            f"/project-programmes/{self.allowed_programme.id}/sections/basic-info/transitions/",
            {"to": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        basic_info.refresh_from_db()
        self.assertEqual(basic_info.status, "COMPLETE")

    def test_restricted_programmer_cannot_update_unassigned_project_programme(self):
        self.client.force_authenticate(user=self.unassigned_user)

        response = self.client.patch(
            f"/project-programmes/{self.unassigned_programme.id}/",
            {"briefProjectProgramme": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_responsible_viewer_can_create_project_programme(self):
        self.client.force_authenticate(user=self.responsible_viewer_user)

        response = self.client.post(
            "/project-programmes/",
            {"project": str(self.responsible_project.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_project_manager_cannot_edit_project_programme_data(self):
        self.client.force_authenticate(user=self.project_manager_user)

        response = self.client.patch(
            f"/project-programmes/{self.allowed_programme.id}/",
            {"briefProjectProgramme": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_project_manager_can_return_project_programme_to_draft(self):
        self.client.force_authenticate(user=self.project_manager_user)
        self.allowed_programme.status = "COMPLETE"
        self.allowed_programme.save()

        response = self.client.post(
            f"/project-programmes/{self.allowed_programme.id}/transitions/",
            {"to": "DRAFT"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.allowed_programme.refresh_from_db()
        self.assertEqual(self.allowed_programme.status, "DRAFT")

    def test_project_manager_cannot_mark_project_programme_complete(self):
        self.client.force_authenticate(user=self.project_manager_user)

        response = self.client.post(
            f"/project-programmes/{self.allowed_programme.id}/transitions/",
            {"to": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_contributor_group_user_can_update_project_programme_without_membership(self):
        self.client.force_authenticate(user=self.contributor_user)

        response = self.client.patch(
            f"/project-programmes/{self.unassigned_programme.id}/",
            {"briefProjectProgramme": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contributor_group_user_can_mark_project_programme_complete_without_membership(self):
        self.client.force_authenticate(user=self.contributor_user)

        response = self.client.post(
            f"/project-programmes/{self.unassigned_programme.id}/transitions/",
            {"to": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contributor_group_user_can_mark_section_complete_without_membership(self):
        self.client.force_authenticate(user=self.contributor_user)
        basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=self.unassigned_programme,
            status="DRAFT",
            projectName="Unassigned",
            district="District",
        )

        response = self.client.post(
            f"/project-programmes/{self.unassigned_programme.id}/sections/basic-info/transitions/",
            {"to": "COMPLETE"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        basic_info.refresh_from_db()
        self.assertEqual(basic_info.status, "COMPLETE")

    def test_project_programme_endpoint_requires_authentication(self):
        response = self.client.get(f"/project-programmes/{self.allowed_programme.id}/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_restricted_programmer_can_create_section_for_assigned_programme(self):
        self.client.force_authenticate(user=self.allowed_user)

        response = self.client.post(
            f"/project-programmes/{self.allowed_programme.id}/sections/basic-info/",
            {
                "projectProgrammeCompiler": "Compiler",
                "personsInvolved": "Person",
                "inspector": "Inspector",
                "estimatedCosts": "100000",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_restricted_programmer_cannot_create_section_for_unassigned_programme(self):
        self.client.force_authenticate(user=self.unassigned_user)

        response = self.client.post(
            f"/project-programmes/{self.unassigned_programme.id}/sections/basic-info/",
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
