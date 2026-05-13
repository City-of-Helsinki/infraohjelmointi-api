from django.test import TestCase
from decimal import Decimal

from infraohjelmointi_api.models import (
    BudgetItem,
    ConstructionHandover,
    ConstructionHandoverFinancing,
    Project
)
from infraohjelmointi_api.models.ConstructionHandoverFinancing import FinancingParty


class ConstructionHandoverFinancingModelTestCase(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name="Construction handover project",
            description="Project used for construction handover financing tests",
        )
        self.handover = ConstructionHandover.objects.create(project=self.project)
        self.budget_item = BudgetItem.objects.create(need=0)

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
