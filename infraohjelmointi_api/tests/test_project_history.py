"""Tests for the per-project change-history endpoint (IO-879 / IO-880 / IO-882).

GET /projects/<id>/history/ exposes the project's AuditLog entries to any user
who can view the project, powering the "Muutoshistoria" UI. This is distinct
from the admin-only /audit-logs/ endpoint, so the permission contract (a plain
viewer may read it) is part of what these tests pin down.
"""
import uuid
from datetime import datetime, timezone

from django.test import TestCase
from django.contrib.auth import get_user_model
from helusers.models import ADGroup
from rest_framework.test import APIRequestFactory, force_authenticate

from infraohjelmointi_api.models import (
    AuditLog,
    ConstructionProcurementMethod,
    Project,
)
from infraohjelmointi_api.views import BaseViewSet
from infraohjelmointi_api.views.ProjectViewSet import ProjectViewSet
from unittest.mock import patch

User = get_user_model()

HISTORY_VIEW = ProjectViewSet.as_view({"get": "get_project_history"})


def _set_created(audit_log, when):
    """createdDate is auto_now_add, so override it via update() for deterministic ordering."""
    AuditLog.objects.filter(pk=audit_log.pk).update(createdDate=when)


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectHistoryEndpointTestCase(TestCase):
    """Behaviour of the history endpoint with auth/permissions patched out."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.actor = User.objects.create(
            first_name="Anna", last_name="Hakala", username="anna", email="anna@example.com"
        )
        self.project = Project.objects.create(
            name="Hakaniemen tori", description="History test project", hkrId=11111
        )
        self.other_project = Project.objects.create(
            name="Other Project", description="Other test project", hkrId=22222
        )

        # Financial change touching 2026
        self.finance_entry = AuditLog.objects.create(
            actor=self.actor, operation="UPDATE", log_level="INFO",
            origin="infrahankkeiden_ohjelmointi", status="SUCCESS", project=self.project,
            old_values={"2026": "100.00"}, new_values={"2026": "250.00"},
            endpoint="/projects/x/",
        )
        # Form field change (phase)
        self.form_entry = AuditLog.objects.create(
            actor=self.actor, operation="UPDATE", log_level="INFO",
            origin="infrahankkeiden_ohjelmointi", status="SUCCESS", project=self.project,
            old_values={"phase": "proposal"}, new_values={"phase": "design"},
            endpoint="/projects/x/",
        )
        # Deletion snapshot touching name + 2026
        self.delete_entry = AuditLog.objects.create(
            actor=self.actor, operation="DELETE", log_level="INFO",
            origin="infrahankkeiden_ohjelmointi", status="SUCCESS", project=self.project,
            old_values={"name": "Hakaniemen tori", "2026": "250.00"}, new_values={},
            endpoint="/projects/x/",
        )
        # Entry on a different project (must never leak into this project's history)
        self.other_entry = AuditLog.objects.create(
            actor=self.actor, operation="UPDATE", log_level="INFO",
            origin="infrahankkeiden_ohjelmointi", status="SUCCESS", project=self.other_project,
            old_values={"2026": "1.00"}, new_values={"2026": "2.00"},
            endpoint="/projects/y/",
        )

        _set_created(self.finance_entry, datetime(2026, 3, 10, 9, 0, tzinfo=timezone.utc))
        _set_created(self.form_entry, datetime(2026, 3, 11, 9, 0, tzinfo=timezone.utc))
        _set_created(self.delete_entry, datetime(2026, 3, 12, 9, 0, tzinfo=timezone.utc))

    def _get(self, pk, **params):
        request = self.factory.get(f"/projects/{pk}/history/", params)
        return HISTORY_VIEW(request, pk=str(pk))

    def test_returns_project_entries_newest_first(self):
        response = self._get(self.project.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 3)
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(
            ids,
            [str(self.delete_entry.id), str(self.form_entry.id), str(self.finance_entry.id)],
        )

    def test_history_is_scoped_to_the_project(self):
        response = self._get(self.project.id)
        returned_ids = {row["id"] for row in response.data["results"]}
        self.assertNotIn(str(self.other_entry.id), returned_ids)

    def test_year_filter_matches_old_or_new_values(self):
        response = self._get(self.project.id, year="2026")
        ids = [row["id"] for row in response.data["results"]]
        # finance_entry (old+new) and delete_entry (old) touch 2026; form_entry does not.
        self.assertEqual(ids, [str(self.delete_entry.id), str(self.finance_entry.id)])

    def test_field_filter_matches_form_field(self):
        response = self._get(self.project.id, field="phase")
        ids = [row["id"] for row in response.data["results"]]
        self.assertEqual(ids, [str(self.form_entry.id)])

    def test_operation_filter(self):
        update_ids = [r["id"] for r in self._get(self.project.id, operation="UPDATE").data["results"]]
        self.assertEqual(set(update_ids), {str(self.finance_entry.id), str(self.form_entry.id)})

        delete_ids = [r["id"] for r in self._get(self.project.id, operation="DELETE").data["results"]]
        self.assertEqual(delete_ids, [str(self.delete_entry.id)])

    def test_changed_fields_exposed(self):
        response = self._get(self.project.id, operation="DELETE")
        self.assertEqual(response.data["results"][0]["changed_fields"], ["2026", "name"])

    def test_empty_project_returns_empty_list(self):
        empty_project = Project.objects.create(
            name="Empty", description="Empty history project", hkrId=33333
        )
        response = self._get(empty_project.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_invalid_uuid_returns_400(self):
        request = self.factory.get("/projects/not-a-uuid/history/")
        response = HISTORY_VIEW(request, pk="not-a-uuid")
        self.assertEqual(response.status_code, 400)

    def test_unknown_project_returns_404(self):
        response = self._get(uuid.uuid4())
        self.assertEqual(response.status_code, 404)


class ProjectHistoryPermissionTestCase(TestCase):
    """The history endpoint must be reachable by non-admin viewers (IO-879)."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.viewer_group = ADGroup.objects.create(
            name="sl_dyn_kymp_sso_io_katselijat", display_name="Viewers"
        )
        self.admin_group = ADGroup.objects.create(
            name="sg_kymp_sso_io_admin", display_name="Admins"
        )
        self.viewer = User.objects.create_user(username="viewer@test.fi", email="viewer@test.fi")
        self.viewer.ad_groups.add(self.viewer_group)
        self.admin = User.objects.create_user(username="admin@test.fi", email="admin@test.fi")
        self.admin.ad_groups.add(self.admin_group)

        self.project = Project.objects.create(
            name="Visible Project", description="Visible test project", hkrId=44444
        )
        AuditLog.objects.create(
            actor=self.admin, operation="UPDATE", log_level="INFO",
            origin="infrahankkeiden_ohjelmointi", status="SUCCESS", project=self.project,
            old_values={"phase": "a"}, new_values={"phase": "b"}, endpoint="/projects/x/",
        )

    def _call_as(self, user):
        request = self.factory.get(f"/projects/{self.project.id}/history/")
        if user is not None:
            force_authenticate(request, user=user)
        return HISTORY_VIEW(request, pk=str(self.project.id))

    def test_viewer_can_read_history(self):
        response = self._call_as(self.viewer)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_admin_can_read_history(self):
        response = self._call_as(self.admin)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_is_denied(self):
        response = self._call_as(None)
        self.assertIn(response.status_code, (401, 403))


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectAuditProducerTestCase(TestCase):
    """The PATCH producer must record the form fields the Muutoshistoria UI shows.

    `description` (Hankkeen kuvaus) and `constructionProcurementMethod`
    (Hankintatapa) are part of the change-history design, so editing them has to
    leave an AuditLog entry the history endpoint can serve.
    """

    def setUp(self):
        self.method_old = ConstructionProcurementMethod.objects.create(value="kilpailutus")
        self.method_new = ConstructionProcurementMethod.objects.create(value="suorahankinta")
        # No hkrId so the PATCH never reaches the ProjectWise sync step.
        self.project = Project.objects.create(
            name="Producer Project",
            description="Original description",
            hkrId=None,
            constructionProcurementMethod=self.method_old,
        )

    def test_patch_records_description_and_procurement_method(self):
        response = self.client.patch(
            f"/projects/{self.project.id}/",
            {
                "description": "Updated description",
                "constructionProcurementMethod": str(self.method_new.id),
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, msg=response.content)

        entry = AuditLog.objects.get(project=self.project, operation="UPDATE")
        self.assertEqual(entry.old_values["description"], "Original description")
        self.assertEqual(entry.new_values["description"], "Updated description")
        self.assertEqual(
            entry.old_values["constructionProcurementMethod"], str(self.method_old.id)
        )
        self.assertEqual(
            entry.new_values["constructionProcurementMethod"], str(self.method_new.id)
        )

    def test_patch_without_audited_fields_creates_no_entry(self):
        response = self.client.patch(
            f"/projects/{self.project.id}/",
            {"address": "Some Street 1"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, msg=response.content)
        self.assertFalse(
            AuditLog.objects.filter(project=self.project, operation="UPDATE").exists()
        )
