from django.test import TestCase
from decimal import Decimal
import uuid
from rest_framework.test import APITestCase
from rest_framework import status

from infraohjelmointi_api.models import (
    ConstructionHandover,
    ConstructionHandoverFinancing,
    Project,
    ProjectTypeQualifier,
)
from infraohjelmointi_api.models.ConstructionHandoverFinancing import FinancingParty
from infraohjelmointi_api.serializers import ConstructionHandoverFinancingSerializer
from infraohjelmointi_api.views.BaseViewSet import BaseViewSet
from unittest.mock import patch


class ConstructionHandoverFinancingModelTestCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Construction handover project",
            description="Project used for construction handover financing tests",
        )
        self.handover = ConstructionHandover.objects.create(project=self.project)
        self.budget_item = ProjectTypeQualifier.objects.create(value="K1")

    # ------------------------------------------------------------------
    # Creation tests
    # ------------------------------------------------------------------

    def test_kymp_financing_row_is_created(self):
        financing = ConstructionHandoverFinancing.objects.create(
            handover=self.handover,
            financingParty=FinancingParty.KYMP,
            budgetItem=self.budget_item,
            projectNumber="HEL-2024-001",
            budget="150000.00",
        )
        retrieved = ConstructionHandoverFinancing.objects.get(pk=financing.pk)
        self.assertEqual(retrieved.financingParty, FinancingParty.KYMP)
        self.assertEqual(retrieved.budgetItem, self.budget_item)
        self.assertEqual(retrieved.projectNumber, "HEL-2024-001")
        self.assertEqual(retrieved.budget, Decimal("150000.00"))
        self.assertEqual(retrieved.description, "")

    def test_non_kymp_financing_row_is_created(self):
        financing = ConstructionHandoverFinancing.objects.create(
            handover=self.handover,
            financingParty=FinancingParty.OTHER,
            description="Muu rahoittaja X",
            budget="50000.00",
        )
        retrieved = ConstructionHandoverFinancing.objects.get(pk=financing.pk)
        self.assertEqual(retrieved.financingParty, FinancingParty.OTHER)
        self.assertIsNone(retrieved.budgetItem)
        self.assertEqual(retrieved.projectNumber, "")
        self.assertEqual(retrieved.description, "Muu rahoittaja X")
        self.assertEqual(retrieved.budget, Decimal("50000.00"))

    def test_financing_row_without_budget_is_allowed(self):
        financing = ConstructionHandoverFinancing.objects.create(
            handover=self.handover,
            financingParty=FinancingParty.HELEN,
        )
        retrieved = ConstructionHandoverFinancing.objects.get(pk=financing.pk)
        self.assertIsNone(retrieved.budget)

    # ------------------------------------------------------------------
    # Cascade delete test
    # ------------------------------------------------------------------

    def test_financing_rows_deleted_when_handover_deleted(self):
        ConstructionHandoverFinancing.objects.create(
            handover=self.handover,
            financingParty=FinancingParty.KYMP,
            budgetItem=self.budget_item,
            projectNumber="HEL-2024-001",
        )
        ConstructionHandoverFinancing.objects.create(
            handover=self.handover,
            financingParty=FinancingParty.ELISA,
        )
        handover_pk = self.handover.pk
        self.assertEqual(
            ConstructionHandoverFinancing.objects.filter(handover=handover_pk).count(),
            2,
        )

        self.handover.delete()

        self.assertFalse(
            ConstructionHandover.objects.filter(pk=handover_pk).exists(),
            msg="ConstructionHandover should be deleted",
        )
        self.assertEqual(
            ConstructionHandoverFinancing.objects.filter(handover_id=handover_pk).count(),
            0,
            msg="Financing rows should be cascade-deleted with the handover",
        )


class ConstructionHandoverFinancingSerializerTestCase(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Construction handover project",
            description="Project used for construction handover financing serializer tests",
        )
        self.handover = ConstructionHandover.objects.create(project=self.project)
        self.budget_item = ProjectTypeQualifier.objects.create(value="K1")

    def test_other_financing_without_description_raises_validation_error(self):
        """Test that OTHER financing party requires description"""
        data = {
            "handover": str(self.handover.id),
            "financingParty": "OTHER",
            "description": "",
            "projectNumber": "",
            "budget": "50000.00",
        }
        serializer = ConstructionHandoverFinancingSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("description", serializer.errors)

    def test_other_financing_with_description_is_valid(self):
        """Test that OTHER financing party with description is valid"""
        data = {
            "handover": str(self.handover.id),
            "financingParty": "OTHER",
            "description": "External funding source",
            "projectNumber": "",
            "budget": "50000.00",
        }
        serializer = ConstructionHandoverFinancingSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_kymp_financing_without_budget_item_is_valid(self):
        """Test that KYMP financing can be created without budgetItem"""
        data = {
            "handover": str(self.handover.id),
            "financingParty": "KYMP",
            "description": "",
            "projectNumber": "HEL-2024-001",
            "budget": "150000.00",
        }
        serializer = ConstructionHandoverFinancingSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_kymp_financing_with_budget_item_is_valid(self):
        """Test that KYMP financing with budgetItem is valid"""
        data = {
            "handover": str(self.handover.id),
            "financingParty": "KYMP",
            "description": "",
            "budgetItemId": str(self.budget_item.id),
            "projectNumber": "HEL-2024-001",
            "budget": "150000.00",
        }
        serializer = ConstructionHandoverFinancingSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ConstructionHandoverFinancingViewSetTestCase(APITestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Construction handover project",
            description="Project used for construction handover financing viewset tests",
        )
        self.budget_item = ProjectTypeQualifier.objects.create(value="K1")

    def _list_items(self, response):
        data = response.data
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data

    def test_create_requires_handover_or_project(self):
        response = self.client.post(
            "/construction-handover-financings/",
            {
                "financingParty": "OTHER",
                "description": "External",
                "projectNumber": "",
                "budget": "1000.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("handover", response.data)

    def test_create_with_project_resolves_latest_active_handover(self):
        older = ConstructionHandover.objects.create(project=self.project, status="DRAFT")
        latest = ConstructionHandover.objects.create(project=self.project, status="SUBMITTED_TO_PROGRAMMER")

        response = self.client.post(
            "/construction-handover-financings/",
            {
                "project": str(self.project.id),
                "financingParty": "KYMP",
                "budgetItemId": str(self.budget_item.id),
                "projectNumber": "HEL-2024-100",
                "budget": "2000.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        row = ConstructionHandoverFinancing.objects.get(id=response.data["id"])
        self.assertEqual(row.handover_id, latest.id)
        self.assertNotEqual(row.handover_id, older.id)

    def test_create_with_project_returns_400_when_no_active_handover_exists(self):
        archived_project = Project.objects.create(
            name="Archived handover project",
            description="Project with only moved handovers",
        )
        ConstructionHandover.objects.create(
            project=archived_project,
            status="MOVED_TO_CONSTRUCTION_PREPARATION",
        )

        response = self.client.post(
            "/construction-handover-financings/",
            {
                "project": str(archived_project.id),
                "financingParty": "OTHER",
                "description": "External",
                "projectNumber": "",
                "budget": "1000.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("project", response.data)

    def test_create_with_invalid_budget_item_id_returns_400(self):
        handover = ConstructionHandover.objects.create(project=self.project, status="DRAFT")

        response = self.client.post(
            "/construction-handover-financings/",
            {
                "handover": str(handover.id),
                "financingParty": "KYMP",
                "budgetItemId": str(uuid.uuid4()),
                "projectNumber": "HEL-2024-200",
                "budget": "2500.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("budgetItemId", response.data)

    def test_create_returns_400_for_locked_handover(self):
        handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
        )

        response = self.client.post(
            "/construction-handover-financings/",
            {
                "handover": str(handover.id),
                "financingParty": "OTHER",
                "description": "External",
                "projectNumber": "",
                "budget": "1000.00",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"][0],
            "Only construction handovers in DRAFT status can be edited.",
        )

    def test_update_returns_400_for_locked_handover(self):
        locked_handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
        )
        financing = ConstructionHandoverFinancing.objects.create(
            handover=locked_handover,
            financingParty=FinancingParty.OTHER,
            description="Before update",
            budget="1000.00",
        )

        response = self.client.patch(
            f"/construction-handover-financings/{financing.id}/",
            {"description": "After update"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"][0],
            "Only construction handovers in DRAFT status can be edited.",
        )

    def test_destroy_returns_409_for_locked_handover(self):
        locked_handover = ConstructionHandover.objects.create(
            project=self.project,
            status="SUBMITTED_TO_PROGRAMMER",
        )
        financing = ConstructionHandoverFinancing.objects.create(
            handover=locked_handover,
            financingParty=FinancingParty.OTHER,
            description="Locked",
            budget="1000.00",
        )

        response = self.client.delete(f"/construction-handover-financings/{financing.id}/")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(
            response.data["detail"],
            "Only construction handovers in DRAFT status can be edited.",
        )

    def test_list_filters_by_handover(self):
        handover_a = ConstructionHandover.objects.create(project=self.project, status="DRAFT")
        handover_b = ConstructionHandover.objects.create(project=self.project, status="DRAFT")

        row_a = ConstructionHandoverFinancing.objects.create(
            handover=handover_a,
            financingParty=FinancingParty.OTHER,
            description="A",
            budget="1000.00",
        )
        ConstructionHandoverFinancing.objects.create(
            handover=handover_b,
            financingParty=FinancingParty.OTHER,
            description="B",
            budget="2000.00",
        )

        response = self.client.get(f"/construction-handover-financings/?handover={handover_a.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = self._list_items(response)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], str(row_a.id))

    def test_list_by_project_excludes_moved_to_construction_preparation(self):
        active_handover = ConstructionHandover.objects.create(project=self.project, status="DRAFT")
        moved_handover = ConstructionHandover.objects.create(
            project=self.project,
            status="MOVED_TO_CONSTRUCTION_PREPARATION",
        )

        active_row = ConstructionHandoverFinancing.objects.create(
            handover=active_handover,
            financingParty=FinancingParty.OTHER,
            description="Active",
            budget="3000.00",
        )
        ConstructionHandoverFinancing.objects.create(
            handover=moved_handover,
            financingParty=FinancingParty.OTHER,
            description="Moved",
            budget="4000.00",
        )

        response = self.client.get(f"/construction-handover-financings/?project={self.project.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = self._list_items(response)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["id"], str(active_row.id))
