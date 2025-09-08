from django.test import TestCase
from datetime import date
from collections import defaultdict
import uuid

from infraohjelmointi_api.models import (
    ProjectClass,
    ClassFinancial,
)
from infraohjelmointi_api.serializers.FinancialSumSerializer import FinancialSumSerializer


class FinancialSumSerializerTestCase(TestCase):
    """Test cases for FinancialSumSerializer budget overlap calculation consistency"""

    def setUp(self):
        """Set up test data that reproduces the TSE 2028 issue"""
        # Create coordinator classes hierarchy: TSE -> TSE 2028
        self.tse_master = ProjectClass.objects.create(
            id=uuid.uuid4(),
            name="TSE",
            path="TSE",
            forCoordinatorOnly=True
        )
        
        self.tse_2028 = ProjectClass.objects.create(
            id=uuid.uuid4(),
            name="TSE 2028",
            parent=self.tse_master,
            path="TSE/TSE 2028",
            forCoordinatorOnly=True
        )
        
        # Create child classes under TSE 2028
        self.child_class_1 = ProjectClass.objects.create(
            id=uuid.uuid4(),
            name="Child Class 1",
            parent=self.tse_2028,
            path="TSE/TSE 2028/Child Class 1",
            forCoordinatorOnly=True
        )
        
        self.child_class_2 = ProjectClass.objects.create(
            id=uuid.uuid4(),
            name="Child Class 2", 
            parent=self.tse_2028,
            path="TSE/TSE 2028/Child Class 2",
            forCoordinatorOnly=True
        )
        
        # Set up the TSE 2028 case: parent has 58,000, children have 30,000 + 28,000 = 58,000
        # This should NOT show budget overlap warning
        year = date.today().year
        
        # TSE 2028 has frame budget of 58,000
        ClassFinancial.objects.create(
            classRelation=self.tse_2028,
            year=year,
            frameBudget=58000,
            budgetChange=0,
            forFrameView=False
        )
        
        # Child 1 has 30,000
        ClassFinancial.objects.create(
            classRelation=self.child_class_1,
            year=year,
            frameBudget=30000,
            budgetChange=0,
            forFrameView=False
        )
        
        # Child 2 has 28,000
        ClassFinancial.objects.create(
            classRelation=self.child_class_2,
            year=year,
            frameBudget=28000,
            budgetChange=0,
            forFrameView=False
        )

    def test_budget_overlap_no_overlap_case(self):
        """Test that TSE 2028 case (58000 = 30000 + 28000) shows no overlap in both views"""
        year = date.today().year
        
        # Create frame_budgets dict as used in coordinator view
        frame_budgets = defaultdict(lambda: 0)
        frame_budgets[f"{year}-{self.tse_2028.id}"] = 58000
        frame_budgets[f"{year}-{self.child_class_1.id}"] = 30000
        frame_budgets[f"{year}-{self.child_class_2.id}"] = 28000
        
        # Test coordinator view logic (new method)
        serializer = FinancialSumSerializer()
        coordinator_result = serializer.get_frameBudget_and_budgetChange_new(
            instance=self.tse_2028,
            year=year,
            for_frame_view=False,
            frame_budgets=frame_budgets
        )
        
        # Test planning view logic (old method)
        planning_result = serializer.get_frameBudget_and_budgetChange(
            instance=self.tse_2028,
            year=year,
            for_frame_view=False
        )
        
        # Both should show NO overlap since 30000 + 28000 = 58000 (exactly equal)
        self.assertFalse(
            coordinator_result["year0"]["isFrameBudgetOverlap"],
            "Coordinator view should not show budget overlap when children sum equals parent budget"
        )
        
        self.assertFalse(
            planning_result["isFrameBudgetOverlap"],
            "Planning view should not show budget overlap when children sum equals parent budget"
        )
        
        # Both methods should return the same result
        self.assertEqual(
            coordinator_result["year0"]["isFrameBudgetOverlap"],
            planning_result["isFrameBudgetOverlap"],
            "Coordinator and planning views should show consistent budget overlap results"
        )

