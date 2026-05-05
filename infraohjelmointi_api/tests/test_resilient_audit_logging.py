"""IO-845 — tests for the resilient_logger dual-write audit pipeline.

Covers:
- The ``audit_log_project_card_changes`` helper writes a row to *both*
  ``AuditLog`` (legacy local table that powers /audit-logs/) and
  ``ResilientLogEntry`` (queue picked up by Plata's submit_unsent_entries
  cron and shipped to Elastic Cloud).
- The X-Request-Id header captured in ``initialize_request`` flows through
  to the resilient log entry's context as ``x_request_id``, and is omitted
  when the header is absent.
- The 0105 data migration callable copies historical AuditLog rows into
  ResilientLogEntry with the same context shape used by live writes.
"""
import importlib
import logging
import uuid
from unittest.mock import patch

from django.apps import apps as django_apps
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from resilient_logger.models import ResilientLogEntry

from infraohjelmointi_api.models import AuditLog, Project, User
from infraohjelmointi_api.views.ProjectViewSet import ProjectViewSet


# Sentinel so callers can pass user=None explicitly and have it forwarded.
_UNSET = object()


@patch.object(ProjectViewSet, "authentication_classes", new=[])
@patch.object(ProjectViewSet, "permission_classes", new=[])
class AuditLogDualWriteTestCase(TestCase):
    """Helper-level dual-write behavior."""

    def setUp(self):
        self.factory = APIRequestFactory()

        self.user = User.objects.create(
            first_name="Audit",
            last_name="Tester",
            username="audit_tester",
            email="audit.tester@example.com",
        )
        self.project = Project.objects.create(
            id=uuid.uuid4(),
            name="Audit Test Project",
            description="for IO-845 tests",
            hkrId=99001,
        )

        self.viewset = ProjectViewSet()
        # action_map is normally populated by DRF's as_view() routing; supply
        # it manually so initialize_request() can resolve self.action.
        self.viewset.action_map = {"patch": "partial_update", "delete": "destroy"}
        self.viewset.request = self.factory.patch("/projects/")
        self.viewset.request._audit_request_id = None

    def _call_helper(self, *, operation, project, old_values, new_values, user=_UNSET, url="/projects/x/"):
        self.viewset.audit_log_project_card_changes(
            old_values,
            new_values,
            project,
            self.user if user is _UNSET else user,
            url,
            operation,
        )

    def test_update_writes_to_both_auditlog_and_resilient_log(self):
        self._call_helper(
            operation="UPDATE",
            project=self.project,
            old_values={"name": "Old"},
            new_values={"name": "New"},
        )

        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertEqual(ResilientLogEntry.objects.count(), 1)

        audit = AuditLog.objects.get()
        self.assertEqual(audit.operation, "UPDATE")
        self.assertEqual(audit.actor_id, self.user.id)
        self.assertEqual(audit.project_id, self.project.id)
        self.assertEqual(audit.old_values, {"name": "Old"})
        self.assertEqual(audit.new_values, {"name": "New"})

        entry = ResilientLogEntry.objects.get()
        self.assertEqual(entry.level, logging.INFO)
        self.assertEqual(entry.message, f"UPDATE on {self.project.name}")
        self.assertEqual(entry.is_sent, False)
        self.assertEqual(entry.context["operation"], "UPDATE")
        self.assertEqual(entry.context["status"], "SUCCESS")
        self.assertEqual(entry.context["old_values"], {"name": "Old"})
        self.assertEqual(entry.context["new_values"], {"name": "New"})
        self.assertEqual(
            entry.context["target"],
            {"type": "project", "id": str(self.project.id), "name": self.project.name},
        )
        self.assertEqual(
            entry.context["actor"],
            {"name": "Audit Tester", "email": "audit.tester@example.com"},
        )
        self.assertNotIn("x_request_id", entry.context)

    def test_delete_carries_target_when_project_already_gone(self):
        # Mirror destroy() flow: project is deleted, helper is called with project=None.
        self._call_helper(
            operation="DELETE",
            project=None,
            old_values={"name": "Disappeared"},
            new_values={},
        )

        entry = ResilientLogEntry.objects.get()
        self.assertEqual(entry.context["operation"], "DELETE")
        self.assertEqual(entry.context["target"], {})
        self.assertEqual(entry.message, "DELETE on unknown")

    def test_finance_update_is_logged_like_a_regular_update(self):
        self._call_helper(
            operation="UPDATE",
            project=self.project,
            old_values={2026: "100.00"},
            new_values={2026: 250.0},
        )

        entry = ResilientLogEntry.objects.get()
        self.assertEqual(entry.context["operation"], "UPDATE")
        self.assertEqual(entry.context["old_values"], {"2026": "100.00"})
        self.assertEqual(entry.context["new_values"], {"2026": 250.0})

    def test_actor_omitted_when_no_user(self):
        self._call_helper(
            operation="UPDATE",
            project=self.project,
            old_values={},
            new_values={},
            user=None,
        )

        audit = AuditLog.objects.get()
        self.assertIsNone(audit.actor_id)

        entry = ResilientLogEntry.objects.get()
        self.assertEqual(entry.context["actor"], {})

    def test_actor_falls_back_to_username_when_name_blank(self):
        anon = User.objects.create(username="just_a_username", email="a@b.c")
        self._call_helper(
            operation="UPDATE",
            project=self.project,
            old_values={},
            new_values={},
            user=anon,
        )

        entry = ResilientLogEntry.objects.get()
        self.assertEqual(
            entry.context["actor"],
            {"name": "just_a_username", "email": "a@b.c"},
        )

    def test_x_request_id_captured_when_header_present(self):
        request = self.factory.patch("/projects/", HTTP_X_REQUEST_ID="trace-abc-123")
        drf_request = self.viewset.initialize_request(request)
        self.viewset.request = drf_request

        self._call_helper(
            operation="UPDATE",
            project=self.project,
            old_values={},
            new_values={},
        )

        entry = ResilientLogEntry.objects.get()
        self.assertEqual(entry.context["x_request_id"], "trace-abc-123")

    def test_x_request_id_omitted_when_header_absent(self):
        request = self.factory.patch("/projects/")
        drf_request = self.viewset.initialize_request(request)
        self.viewset.request = drf_request

        self._call_helper(
            operation="UPDATE",
            project=self.project,
            old_values={},
            new_values={},
        )

        entry = ResilientLogEntry.objects.get()
        self.assertNotIn("x_request_id", entry.context)


class AuditLogDataMigrationTestCase(TestCase):
    """The 0105 migration callable backfills ResilientLogEntry from AuditLog."""

    def setUp(self):
        self.user = User.objects.create(
            first_name="Hist",
            last_name="Orical",
            username="historical",
            email="hist@example.com",
        )
        self.project = Project.objects.create(
            id=uuid.uuid4(),
            name="Historical Project",
            description="historical project for migration test",
            hkrId=88001,
        )

        self.legacy_a = AuditLog.objects.create(
            actor=self.user,
            operation="UPDATE",
            log_level="INFO",
            origin="infrahankkeiden_ohjelmointi",
            status="SUCCESS",
            project=self.project,
            old_values={"name": "A0"},
            new_values={"name": "A1"},
            endpoint="/projects/a/",
        )
        self.legacy_b = AuditLog.objects.create(
            actor=None,
            operation="DELETE",
            log_level="INFO",
            origin="infrahankkeiden_ohjelmointi",
            status="SUCCESS",
            project=None,
            old_values={"name": "B"},
            new_values={},
            endpoint="/projects/b/",
        )

    def _get_migration_module(self):
        # Migration filename starts with a digit, so we can't `from x import y`
        # — go through importlib.
        return importlib.import_module(
            "infraohjelmointi_api.migrations.0105_migrate_auditlog_to_resilient_logger"
        )

    def test_migration_copies_historical_rows_into_resilient_log(self):
        module = self._get_migration_module()

        module.migrate_auditlog_to_resilient_logger(django_apps, schema_editor=None)

        self.assertEqual(ResilientLogEntry.objects.count(), 2)

        a_copy = ResilientLogEntry.objects.get(
            context__orig_entry_id=str(self.legacy_a.id)
        )
        self.assertEqual(a_copy.is_sent, False)
        self.assertEqual(a_copy.level, logging.INFO)
        self.assertEqual(a_copy.message, "UPDATE on Historical Project")
        self.assertEqual(a_copy.context["operation"], "UPDATE")
        self.assertEqual(a_copy.context["status"], "SUCCESS")
        self.assertEqual(a_copy.context["old_values"], {"name": "A0"})
        self.assertEqual(a_copy.context["new_values"], {"name": "A1"})
        self.assertEqual(a_copy.context["endpoint"], "/projects/a/")
        self.assertEqual(
            a_copy.context["target"],
            {"type": "project", "id": str(self.project.id), "name": self.project.name},
        )
        self.assertEqual(
            a_copy.context["actor"],
            {"name": "Hist Orical", "email": "hist@example.com"},
        )
        self.assertIn("orig_created_at", a_copy.context)
        self.assertTrue(a_copy.context["orig_created_at"].endswith("Z"))

        b_copy = ResilientLogEntry.objects.get(
            context__orig_entry_id=str(self.legacy_b.id)
        )
        self.assertEqual(b_copy.message, "DELETE on unknown")
        self.assertEqual(b_copy.context["target"], {})
        self.assertEqual(b_copy.context["actor"], {})

    def test_migration_is_idempotent_only_in_the_sense_that_reverse_is_a_noop(self):
        # The forward migration intentionally does not de-dupe — running it
        # twice would duplicate the backfill. This test pins that contract so
        # nobody flips it accidentally without thinking through the cron.
        module = self._get_migration_module()
        module.migrate_auditlog_to_resilient_logger(django_apps, schema_editor=None)
        module.migrate_auditlog_to_resilient_logger(django_apps, schema_editor=None)

        self.assertEqual(ResilientLogEntry.objects.count(), 4)
