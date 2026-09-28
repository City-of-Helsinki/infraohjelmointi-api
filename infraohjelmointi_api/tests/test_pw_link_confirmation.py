"""Tests for the PW link confirmation (IO-935).

A mistyped hkrId (PW hanketunnus) used to be synced straight to PW, silently
overwriting another PW project's data. The UI now looks the PW project up via
GET /projects/pw-project-name/?hkrId=..., shows its "Kohde" to the user, and on
OK sends the same id back as `confirmedHkrId`. The API refuses to set or change
an hkrId without that confirmation while PW sync is enabled.
"""
import os
import uuid
from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth import get_user_model
from django.test import TestCase
from helusers.models import ADGroup
from rest_framework.test import APIRequestFactory, force_authenticate

from ..models import Project, ProjectCategory, ProjectClass, ProjectPhase, ProjectType
from ..services.ProjectWiseService import (
    PWProjectNotFoundError,
    PWProjectResponseError,
    ProjectWiseService,
)
from ..views import BaseViewSet
from ..views.ProjectViewSet import ProjectViewSet

User = get_user_model()

PW_PROJECT_NAME_VIEW = ProjectViewSet.as_view({"get": "get_pw_project_name"})

PW_SYNC_ON = {"PW_SYNC_ENABLED": "True"}
SYNC_TO_PW = "infraohjelmointi_api.views.ProjectViewSet.ProjectWiseService.sync_project_to_pw"
NAME_FROM_PW = (
    "infraohjelmointi_api.views.ProjectViewSet.ProjectWiseService.get_project_name_from_pw"
)


class _ProjectFixtureMixin:
    def _create_project(self, **kwargs):
        project_class, _ = ProjectClass.objects.get_or_create(
            name="PW Link Test Class", defaults={"path": "PW/Link/Test/Class"}
        )
        defaults = dict(
            id=uuid.uuid4(),
            name="Link Test Project",
            description="Original description",
            programmed=True,
            planningStartYear=2024,
            constructionEndYear=2030,
            projectClass=project_class,
            type=ProjectType.objects.get_or_create(value="park")[0],
            phase=ProjectPhase.objects.get_or_create(value="programming")[0],
            category=ProjectCategory.objects.get_or_create(value="basic")[0],
        )
        defaults.update(kwargs)
        return Project.objects.create(**defaults)


@patch.dict(os.environ, PW_SYNC_ON)
@patch(SYNC_TO_PW)
@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class PWLinkConfirmationGuardTestCase(_ProjectFixtureMixin, TestCase):
    def setUp(self):
        self.project_without_hkr = self._create_project(hkrId=None)
        self.project_with_hkr = self._create_project(name="Linked Project", hkrId=5050)

    def _patch(self, project, data):
        return self.client.patch(
            f"/projects/{project.id}/", data, content_type="application/json"
        )

    def test_new_hkr_id_without_confirmation_is_refused(self, mock_sync):
        response = self._patch(self.project_without_hkr, {"hkrId": 1234})

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(response.json(), {"hkrId": ["PW_LINK_NOT_CONFIRMED"]})
        mock_sync.assert_not_called()
        self.project_without_hkr.refresh_from_db()
        self.assertIsNone(self.project_without_hkr.hkrId)

    def test_new_hkr_id_with_matching_confirmation_is_saved_and_synced(self, mock_sync):
        response = self._patch(
            self.project_without_hkr, {"hkrId": 1234, "confirmedHkrId": "1234"}
        )

        self.assertEqual(response.status_code, 200, msg=response.content)
        mock_sync.assert_called_once()
        self.project_without_hkr.refresh_from_db()
        self.assertEqual(self.project_without_hkr.hkrId, 1234)

    def test_confirmation_for_a_different_id_is_refused(self, mock_sync):
        response = self._patch(
            self.project_without_hkr, {"hkrId": 1234, "confirmedHkrId": 4321}
        )

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(response.json(), {"hkrId": ["PW_LINK_NOT_CONFIRMED"]})
        mock_sync.assert_not_called()

    def test_changing_an_existing_hkr_id_needs_confirmation(self, mock_sync):
        response = self._patch(self.project_with_hkr, {"hkrId": 6060})

        self.assertEqual(response.status_code, 400, msg=response.content)
        mock_sync.assert_not_called()
        self.project_with_hkr.refresh_from_db()
        self.assertEqual(self.project_with_hkr.hkrId, 5050)

    def test_editing_other_fields_of_a_linked_project_needs_no_confirmation(self, mock_sync):
        response = self._patch(self.project_with_hkr, {"description": "Edited"})

        self.assertEqual(response.status_code, 200, msg=response.content)
        mock_sync.assert_called_once()

    def test_resending_the_current_hkr_id_needs_no_confirmation(self, mock_sync):
        response = self._patch(self.project_with_hkr, {"hkrId": "5050"})

        self.assertEqual(response.status_code, 200, msg=response.content)

    def test_clearing_the_hkr_id_needs_no_confirmation(self, mock_sync):
        response = self._patch(self.project_with_hkr, {"hkrId": None})

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.project_with_hkr.refresh_from_db()
        self.assertIsNone(self.project_with_hkr.hkrId)

    def test_create_with_unconfirmed_hkr_id_is_refused(self, mock_sync):
        response = self.client.post(
            "/projects/",
            {"name": "New Project", "description": "New", "hkrId": 7070},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(response.json(), {"hkrId": ["PW_LINK_NOT_CONFIRMED"]})
        self.assertFalse(Project.objects.filter(name="New Project").exists())

    def test_create_with_confirmed_hkr_id_succeeds(self, mock_sync):
        response = self.client.post(
            "/projects/",
            {
                "name": "New Project",
                "description": "New",
                "hkrId": 7070,
                "confirmedHkrId": 7070,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201, msg=response.content)
        self.assertEqual(Project.objects.get(name="New Project").hkrId, 7070)

    def test_bulk_update_with_unconfirmed_hkr_id_is_refused(self, mock_sync):
        response = self.client.patch(
            "/projects/bulk-update/",
            [{"id": str(self.project_without_hkr.id), "data": {"hkrId": 8080}}],
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(response.json(), {"hkrId": ["PW_LINK_NOT_CONFIRMED"]})
        mock_sync.assert_not_called()
        self.project_without_hkr.refresh_from_db()
        self.assertIsNone(self.project_without_hkr.hkrId)

    def test_bulk_update_with_confirmed_hkr_id_succeeds(self, mock_sync):
        response = self.client.patch(
            "/projects/bulk-update/",
            [
                {
                    "id": str(self.project_without_hkr.id),
                    "data": {"hkrId": 8080, "confirmedHkrId": 8080},
                }
            ],
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.project_without_hkr.refresh_from_db()
        self.assertEqual(self.project_without_hkr.hkrId, 8080)

    def test_put_with_unconfirmed_hkr_id_is_refused(self, mock_sync):
        response = self.client.put(
            f"/projects/{self.project_without_hkr.id}/",
            {"name": "Link Test Project", "description": "Put", "hkrId": 9090},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertEqual(response.json(), {"hkrId": ["PW_LINK_NOT_CONFIRMED"]})
        self.project_without_hkr.refresh_from_db()
        self.assertIsNone(self.project_without_hkr.hkrId)

    def test_put_with_confirmed_hkr_id_is_saved(self, mock_sync):
        response = self.client.put(
            f"/projects/{self.project_without_hkr.id}/",
            {
                "name": "Link Test Project",
                "description": "Put",
                "hkrId": 9090,
                "confirmedHkrId": 9090,
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.project_without_hkr.refresh_from_db()
        self.assertEqual(self.project_without_hkr.hkrId, 9090)

    def test_the_same_id_with_a_leading_zero_is_not_a_change(self, mock_sync):
        response = self._patch(self.project_with_hkr, {"hkrId": "05050"})

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.project_with_hkr.refresh_from_db()
        self.assertEqual(self.project_with_hkr.hkrId, 5050)

    def test_confirmation_is_compared_as_a_number(self, mock_sync):
        response = self._patch(
            self.project_without_hkr, {"hkrId": 1234, "confirmedHkrId": " 01234 "}
        )

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.project_without_hkr.refresh_from_db()
        self.assertEqual(self.project_without_hkr.hkrId, 1234)

    def test_malformed_hkr_id_gets_the_serializer_error_not_the_pw_code(self, mock_sync):
        response = self._patch(self.project_without_hkr, {"hkrId": "abc"})

        self.assertEqual(response.status_code, 400, msg=response.content)
        self.assertNotIn("PW_LINK_NOT_CONFIRMED", response.json().get("hkrId", []))
        mock_sync.assert_not_called()


@patch(SYNC_TO_PW)
@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class PWLinkConfirmationSyncDisabledTestCase(_ProjectFixtureMixin, TestCase):
    """With PW sync off nothing is written to PW, so no confirmation is needed."""

    @patch.dict(os.environ, {"PW_SYNC_ENABLED": "False"})
    def test_new_hkr_id_is_saved_without_confirmation(self, mock_sync):
        project = self._create_project(hkrId=None)

        response = self.client.patch(
            f"/projects/{project.id}/", {"hkrId": 1234}, content_type="application/json"
        )

        self.assertEqual(response.status_code, 200, msg=response.content)
        project.refresh_from_db()
        self.assertEqual(project.hkrId, 1234)


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class PWProjectNameLookupTestCase(TestCase):
    URL = "/projects/pw-project-name/"

    @patch.dict(os.environ, PW_SYNC_ON)
    @patch(NAME_FROM_PW, return_value="Mannerheimintie peruskorjaus")
    def test_returns_pw_kohde(self, mock_name):
        response = self.client.get(self.URL, {"hkrId": " 1234 "})

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(
            response.json(),
            {"hkrId": "1234", "name": "Mannerheimintie peruskorjaus", "syncEnabled": True},
        )
        mock_name.assert_called_once_with("1234")

    @patch.dict(os.environ, PW_SYNC_ON)
    @patch(NAME_FROM_PW, side_effect=PWProjectNotFoundError("not found"))
    def test_unknown_hkr_id_returns_404(self, mock_name):
        response = self.client.get(self.URL, {"hkrId": "1234"})

        self.assertEqual(response.status_code, 404, msg=response.content)
        self.assertEqual(response.json(), {"hkrId": ["PW_PROJECT_NOT_FOUND"]})

    @patch.dict(os.environ, PW_SYNC_ON)
    @patch(NAME_FROM_PW, side_effect=PWProjectResponseError("PW responded with 503"))
    def test_pw_outage_returns_502(self, mock_name):
        response = self.client.get(self.URL, {"hkrId": "1234"})

        self.assertEqual(response.status_code, 502, msg=response.content)
        self.assertEqual(response.json(), {"hkrId": ["PW_UNAVAILABLE"]})

    @patch.dict(os.environ, PW_SYNC_ON)
    @patch(NAME_FROM_PW, return_value="Kohde")
    def test_looks_up_the_id_without_leading_zeros(self, mock_name):
        response = self.client.get(self.URL, {"hkrId": "01234"})

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(response.json()["hkrId"], "1234")
        mock_name.assert_called_once_with("1234")

    @patch.dict(os.environ, PW_SYNC_ON)
    @patch(
        "infraohjelmointi_api.views.ProjectViewSet.ProjectWiseService.get_project_from_pw",
        side_effect=requests.ConnectionError("PW host unreachable"),
    )
    def test_pw_connection_error_returns_502_not_500(self, mock_get):
        response = self.client.get(self.URL, {"hkrId": "1234"})

        self.assertEqual(response.status_code, 502, msg=response.content)
        self.assertEqual(response.json(), {"hkrId": ["PW_UNAVAILABLE"]})

    @patch(NAME_FROM_PW)
    def test_invalid_hkr_id_returns_400_without_calling_pw(self, mock_name):
        for value in ["", "abc", "-5", "12.5", "²"]:
            with self.subTest(value=value):
                response = self.client.get(self.URL, {"hkrId": value})
                self.assertEqual(response.status_code, 400, msg=response.content)
                self.assertEqual(response.json(), {"hkrId": ["INVALID_HKR_ID"]})
        mock_name.assert_not_called()

    @patch.dict(os.environ, {"PW_SYNC_ENABLED": "False"})
    @patch(NAME_FROM_PW)
    def test_sync_disabled_skips_pw(self, mock_name):
        response = self.client.get(self.URL, {"hkrId": "1234"})

        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertEqual(
            response.json(), {"hkrId": "1234", "name": None, "syncEnabled": False}
        )
        mock_name.assert_not_called()


class PWProjectNameLookupPermissionTestCase(TestCase):
    """Only roles that can set an hkrId may use the lookup."""

    def setUp(self):
        self.factory = APIRequestFactory()
        viewer_group = ADGroup.objects.create(
            name="sl_dyn_kymp_sso_io_katselijat", display_name="Viewers"
        )
        planner_group = ADGroup.objects.create(
            name="sg_kymp_sso_io_ohjelmoijat", display_name="Planners"
        )
        self.viewer = User.objects.create_user(username="viewer@test.fi", email="viewer@test.fi")
        self.viewer.ad_groups.add(viewer_group)
        self.planner = User.objects.create_user(
            username="planner@test.fi", email="planner@test.fi"
        )
        self.planner.ad_groups.add(planner_group)

    def _call_as(self, user):
        request = self.factory.get("/projects/pw-project-name/", {"hkrId": "1234"})
        if user is not None:
            force_authenticate(request, user=user)
        return PW_PROJECT_NAME_VIEW(request)

    @patch.dict(os.environ, {"PW_SYNC_ENABLED": "False"})
    def test_planner_can_look_up(self):
        self.assertEqual(self._call_as(self.planner).status_code, 200)

    def test_viewer_is_denied(self):
        self.assertEqual(self._call_as(self.viewer).status_code, 403)

    def test_anonymous_is_denied(self):
        self.assertIn(self._call_as(None).status_code, (401, 403))


class GetProjectNameFromPWTestCase(TestCase):
    def setUp(self):
        self.service = ProjectWiseService()

    def test_returns_kohde_from_related_instance_properties(self):
        with patch.object(
            self.service,
            "get_project_from_pw",
            return_value={
                "relationshipInstances": [
                    {"relatedInstance": {"properties": {"PROJECT_Kohde": "Kohde X"}}}
                ]
            },
        ) as mock_get:
            self.assertEqual(self.service.get_project_name_from_pw("1234"), "Kohde X")
        mock_get.assert_called_once_with(
            "1234", timeout=ProjectWiseService.PW_NAME_LOOKUP_TIMEOUT_SECONDS
        )

    def test_passes_the_timeout_to_pw(self):
        self.service.session = MagicMock()
        self.service.session.get.return_value.status_code = 200
        self.service.session.get.return_value.json.return_value = {
            "instances": [
                {"relationshipInstances": [{"relatedInstance": {"properties": {"PROJECT_Kohde": "K"}}}]}
            ]
        }

        self.assertEqual(self.service.get_project_name_from_pw("1234"), "K")
        self.assertEqual(
            self.service.session.get.call_args.kwargs["timeout"],
            ProjectWiseService.PW_NAME_LOOKUP_TIMEOUT_SECONDS,
        )

    def test_returns_none_when_pw_has_no_relationship_instances(self):
        with patch.object(
            self.service, "get_project_from_pw", return_value={"relationshipInstances": []}
        ):
            self.assertIsNone(self.service.get_project_name_from_pw("1234"))

    def test_outages_and_malformed_responses_become_response_errors(self):
        for error in [
            requests.ConnectionError("down"),
            requests.Timeout("slow"),
            ValueError("not json"),
            KeyError("instances"),
        ]:
            with self.subTest(error=type(error).__name__):
                with patch.object(self.service, "get_project_from_pw", side_effect=error):
                    with self.assertRaises(PWProjectResponseError):
                        self.service.get_project_name_from_pw("1234")

    def test_returns_none_when_kohde_is_missing(self):
        with patch.object(
            self.service,
            "get_project_from_pw",
            return_value={"relationshipInstances": [{"relatedInstance": {"properties": {}}}]},
        ):
            self.assertIsNone(self.service.get_project_name_from_pw("1234"))

    def test_propagates_not_found(self):
        with patch.object(
            self.service,
            "get_project_from_pw",
            side_effect=PWProjectNotFoundError("not found"),
        ):
            with self.assertRaises(PWProjectNotFoundError):
                self.service.get_project_name_from_pw("1234")
