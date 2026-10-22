"""Tests for the per-handover change-history feed.

GET /construction-handovers/<id>/history/ reconstructs who-changed-what-when
events from the handover's django-simple-history rows. The reconstruction is
non-trivial because `HistoricalModel.save()` deletes the creation row and
rewrites each update row to hold the *previous* snapshot with the previous
editor as `history_user`; these tests pin that reconstruction down, plus the
endpoint shape and the permission contract (the handover tab, and therefore its
history, is not exposed to plain viewers).
"""
import uuid

from django.test import TestCase
from django.contrib.auth import get_user_model
from helusers.models import ADGroup
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate

from infraohjelmointi_api.models import (
    ConstructionHandover,
    ConstructionProcurementMethod,
    Person,
    Project,
)
from infraohjelmointi_api.services.ConstructionHandoverHistoryService import (
    build_history,
)
from infraohjelmointi_api.views import BaseViewSet
from infraohjelmointi_api.views.ConstructionHandoverViewSet import (
    ConstructionHandoverViewSet,
)
from unittest.mock import patch

User = get_user_model()

HISTORY_VIEW = ConstructionHandoverViewSet.as_view(
    {"get": "get_construction_handover_history"}
)


class ConstructionHandoverHistoryServiceTestCase(TestCase):
    """The reconstruction of events from simple-history rows."""

    def setUp(self):
        self.user_1 = User.objects.create(
            username="hist_user_1", first_name="Anna", last_name="Hakala",
            email="anna@example.com",
        )
        self.user_2 = User.objects.create(
            username="hist_user_2", first_name="Pekka", last_name="Virtanen",
            email="pekka@example.com",
        )
        self.person = Person.objects.create(
            firstName="Liisa", lastName="Korhonen", email="liisa@example.com",
            title="Planner", phone="0100000000",
        )
        self.method = ConstructionProcurementMethod.objects.create(value="Kilpailutus")
        self.project = Project.objects.create(
            name="History project", description="Handover history test project",
        )

    def _create(self, **kwargs):
        return ConstructionHandover.objects.create(
            project=self.project,
            createdBy=self.user_1,
            updatedBy=self.user_1,
            **kwargs,
        )

    def test_creation_only_yields_a_single_create_event(self):
        handover = self._create(name="Alku")

        events = build_history(handover)

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["operation"], "CREATE")
        self.assertEqual(events[0]["changed_fields"], [])
        self.assertEqual(events[0]["old_values"], {})
        self.assertEqual(events[0]["new_values"], {})
        self.assertEqual(events[0]["actor_first_name"], "Anna")
        self.assertEqual(events[0]["actor_last_name"], "Hakala")

    def test_single_field_update(self):
        handover = self._create(name="Alku")
        handover.name = "Loppu"
        handover.updatedBy = self.user_1
        handover.save()

        events = build_history(handover)

        # newest first: the update, then the creation
        self.assertEqual([e["operation"] for e in events], ["UPDATE", "CREATE"])
        update = events[0]
        self.assertEqual(update["changed_fields"], ["name"])
        self.assertEqual(update["old_values"], {"name": "Alku"})
        self.assertEqual(update["new_values"], {"name": "Loppu"})
        self.assertEqual(update["actor_username"], "hist_user_1")

    def test_multiple_updates_attribute_the_right_actor_each(self):
        handover = self._create(name="A")

        handover.name = "B"
        handover.updatedBy = self.user_2
        handover.save()

        handover.name = "C"
        handover.updatedBy = self.user_1
        handover.save()

        events = build_history(handover)

        self.assertEqual([e["operation"] for e in events], ["UPDATE", "UPDATE", "CREATE"])
        # newest update B -> C by user_1
        self.assertEqual(events[0]["old_values"], {"name": "B"})
        self.assertEqual(events[0]["new_values"], {"name": "C"})
        self.assertEqual(events[0]["actor_username"], "hist_user_1")
        # earlier update A -> B by user_2
        self.assertEqual(events[1]["old_values"], {"name": "A"})
        self.assertEqual(events[1]["new_values"], {"name": "B"})
        self.assertEqual(events[1]["actor_username"], "hist_user_2")

    def test_status_transition_is_captured(self):
        handover = self._create(name="A", status="DRAFT")
        handover.status = "SUBMITTED_TO_PROGRAMMER"
        handover.updatedBy = self.user_2
        handover.save()

        events = build_history(handover)

        self.assertEqual(events[0]["changed_fields"], ["status"])
        self.assertEqual(events[0]["old_values"], {"status": "DRAFT"})
        self.assertEqual(events[0]["new_values"], {"status": "SUBMITTED_TO_PROGRAMMER"})
        self.assertEqual(events[0]["actor_username"], "hist_user_2")

    def test_relation_changes_are_resolved_to_readable_values(self):
        handover = self._create(name="A")

        handover.personPlanning = self.person
        handover.constructionProcurementMethod = self.method
        handover.updatedBy = self.user_1
        handover.save()

        events = build_history(handover)

        update = events[0]
        self.assertEqual(set(update["changed_fields"]), {"personPlanning", "constructionProcurementMethod"})
        self.assertIsNone(update["old_values"]["personPlanning"])
        self.assertEqual(update["new_values"]["personPlanning"], "Liisa Korhonen")
        self.assertIsNone(update["old_values"]["constructionProcurementMethod"])
        self.assertEqual(update["new_values"]["constructionProcurementMethod"], "Kilpailutus")

    def test_no_op_save_produces_no_event(self):
        handover = self._create(name="A")
        # Touch only an untracked aspect: re-save with the same tracked values.
        handover.updatedBy = self.user_2
        handover.save()

        events = build_history(handover)

        self.assertEqual([e["operation"] for e in events], ["CREATE"])


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ConstructionHandoverHistoryEndpointTestCase(TestCase):
    """Endpoint behaviour with auth/permissions patched out."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            username="ep_user", first_name="Anna", last_name="Hakala",
            email="anna-ep@example.com",
        )
        self.project = Project.objects.create(
            name="Endpoint project", description="Endpoint history test project",
        )
        self.handover = ConstructionHandover.objects.create(
            project=self.project, name="A", createdBy=self.user, updatedBy=self.user,
        )
        self.handover.name = "B"
        self.handover.updatedBy = self.user
        self.handover.save()

    def test_returns_events_newest_first(self):
        response = self.client.get(f"/construction-handovers/{self.handover.id}/history/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["results"][0]["operation"], "UPDATE")
        self.assertEqual(response.data["results"][1]["operation"], "CREATE")

    def test_invalid_uuid_returns_400(self):
        response = self.client.get("/construction-handovers/not-a-uuid/history/")
        self.assertEqual(response.status_code, 400)

    def test_unknown_handover_returns_404(self):
        response = self.client.get(f"/construction-handovers/{uuid.uuid4()}/history/")
        self.assertEqual(response.status_code, 404)


class ConstructionHandoverHistoryPermissionTestCase(TestCase):
    """The history feed rides with the handover read permission: planners (and
    other handover-capable roles) may read it, plain viewers and anonymous
    users may not (the handover tab is hidden from viewers)."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.planner_group = ADGroup.objects.create(
            name="sg_kymp_sso_io_ohjelmoijat", display_name="Planners"
        )
        self.viewer_group = ADGroup.objects.create(
            name="sl_dyn_kymp_sso_io_katselijat", display_name="Viewers"
        )
        self.planner = User.objects.create_user(username="planner@test.fi", email="planner@test.fi")
        self.planner.ad_groups.add(self.planner_group)
        self.viewer = User.objects.create_user(username="viewer@test.fi", email="viewer@test.fi")
        self.viewer.ad_groups.add(self.viewer_group)

        self.project = Project.objects.create(
            name="Permission project", description="Permission history test project",
        )
        self.handover = ConstructionHandover.objects.create(
            project=self.project, name="A", createdBy=self.planner, updatedBy=self.planner,
        )

    def _call_as(self, user):
        request = self.factory.get(f"/construction-handovers/{self.handover.id}/history/")
        if user is not None:
            force_authenticate(request, user=user)
        return HISTORY_VIEW(request, pk=str(self.handover.id))

    def test_planner_can_read_history(self):
        response = self._call_as(self.planner)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)

    def test_viewer_is_denied(self):
        response = self._call_as(self.viewer)
        self.assertIn(response.status_code, (401, 403))

    def test_anonymous_is_denied(self):
        response = self._call_as(None)
        self.assertIn(response.status_code, (401, 403))
