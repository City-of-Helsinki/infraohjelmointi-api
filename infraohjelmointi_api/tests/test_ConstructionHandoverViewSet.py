from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from infraohjelmointi_api.models import ConstructionHandover, Project
from infraohjelmointi_api.serializers import (
    ConstructionHandoverCreateSerializer,
    ConstructionHandoverGetSerializer,
    ConstructionHandoverUpdateSerializer,
)
from infraohjelmointi_api.views.BaseViewSet import BaseViewSet
from infraohjelmointi_api.views.ConstructionHandoverViewSet import ConstructionHandoverViewSet

User = get_user_model()


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ConstructionHandoverViewSetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.project = Project.objects.create(
            name="Construction handover project",
            description="Project used for construction handover view set tests",
        )
        self.user_1 = User.objects.create(
            username="handover_user_1",
            first_name="Handover",
            last_name="User One",
            email="handover1@example.com",
        )
        self.user_2 = User.objects.create(
            username="handover_user_2",
            first_name="Handover",
            last_name="User Two",
            email="handover2@example.com",
        )

    def test_get_serializer_class_by_action(self):
        viewset = ConstructionHandoverViewSet()

        viewset.action = "list"
        self.assertEqual(viewset.get_serializer_class(), ConstructionHandoverGetSerializer)

        viewset.action = "retrieve"
        self.assertEqual(viewset.get_serializer_class(), ConstructionHandoverGetSerializer)

        viewset.action = "create"
        self.assertEqual(viewset.get_serializer_class(), ConstructionHandoverCreateSerializer)

        viewset.action = "update"
        self.assertEqual(viewset.get_serializer_class(), ConstructionHandoverUpdateSerializer)

        viewset.action = "partial_update"
        self.assertEqual(viewset.get_serializer_class(), ConstructionHandoverUpdateSerializer)

    def test_get_construction_handover_by_id(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            name="Test handover",
        )

        response = self.client.get(f"/construction-handovers/{handover.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(handover.id))
        self.assertEqual(response.data["name"], "Test handover")
        self.assertEqual(response.data["status"], "DRAFT")

    def test_create_construction_handover(self):
        self.client.force_authenticate(user=self.user_1)

        response = self.client.post(
            "/construction-handovers/",
            {"project": str(self.project.id)},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        handover = ConstructionHandover.objects.get(id=response.data["id"])
        self.assertEqual(handover.createdBy_id, self.user_1.uuid)
        self.assertEqual(handover.updatedBy_id, self.user_1.uuid)

    def test_partial_update_returns_409_for_non_draft(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
            name="Before update",
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {"name": "After update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "Only construction handovers in DRAFT status can be edited.",
        )

        handover.refresh_from_db()
        self.assertEqual(handover.name, "Before update")

    def test_partial_update_allows_draft(self):
        self.client.force_authenticate(user=self.user_2)

        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
            name="Before update",
            createdBy=self.user_1,
            updatedBy=self.user_1,
        )

        response = self.client.patch(
            f"/construction-handovers/{handover.id}/",
            {"name": "After update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        handover.refresh_from_db()
        self.assertEqual(handover.name, "After update")
        self.assertEqual(handover.createdBy_id, self.user_1.uuid)
        self.assertEqual(handover.updatedBy_id, self.user_2.uuid)

    def test_destroy_returns_409_for_non_draft(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
        )

        response = self.client.delete(f"/construction-handovers/{handover.id}/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "Only construction handovers in DRAFT status can be deleted.",
        )
        self.assertTrue(ConstructionHandover.objects.filter(id=handover.id).exists())

    def test_destroy_allows_draft(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="DRAFT",
        )

        response = self.client.delete(f"/construction-handovers/{handover.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ConstructionHandover.objects.filter(id=handover.id).exists())
