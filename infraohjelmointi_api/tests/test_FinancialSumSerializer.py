from django.test import TestCase
from datetime import date
from collections import defaultdict
import uuid
from unittest.mock import patch

from infraohjelmointi_api.models import (
    ProjectClass,
    ClassFinancial,
    ProjectGroup,
    Project,
    ProjectFinancial,
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
        
        # Test with frame_budgets context (unified method)
        serializer = FinancialSumSerializer()
        result_with_context = serializer.get_frameBudget_and_budgetChange(
            instance=self.tse_2028,
            year=year,
            for_frame_view=False,
            frame_budgets=frame_budgets
        )
        
        # Should show NO overlap since 30000 + 28000 = 58000 (exactly equal)
        self.assertFalse(
            result_with_context["year0"]["isFrameBudgetOverlap"],
            "Should not show budget overlap when children sum equals parent budget (TSE-2028 scenario)"
        )

    @patch("infraohjelmointi_api.serializers.FinancialSumSerializer.CacheService.set_financial_sum")
    @patch("infraohjelmointi_api.serializers.FinancialSumSerializer.CacheService.get_financial_sum")
    def test_project_group_finance_sums_bypass_cache(self, mock_get_financial_sum, mock_set_financial_sum):
        """Regression test: ProjectGroup sums must be calculated fresh and bypass cache."""
        year = date.today().year

        project_group = ProjectGroup.objects.create(name="Group A")
        project = Project.objects.create(
            name="Group project",
            description="Project in group",
            projectGroup=project_group,
            programmed=True,
        )
        ProjectFinancial.objects.create(
            project=project,
            year=year,
            value=1234,
            forFrameView=False,
        )

        mock_get_financial_sum.return_value = {
            "year0": {"plannedBudget": 999999},
            "year": year,
        }

        serializer = FinancialSumSerializer(
            context={
                "finance_year": year,
                "forcedToFrame": False,
                "for_coordinator": False,
                "frame_budgets": defaultdict(lambda: 0),
            }
        )

        result = serializer.get_finance_sums(project_group)

        self.assertEqual(result["year0"]["plannedBudget"], 1234)
        mock_get_financial_sum.assert_not_called()
        mock_set_financial_sum.assert_not_called()

    def test_planning_masterclass_sums_descendant_projects_across_deep_levels(self):
        """Regression: masterclass planning sums must include projects deeper than 2 levels."""
        year = date.today().year

        root_master = ProjectClass.objects.create(
            id=uuid.uuid4(),
            name="8 08 Projektialueet",
            path="8 08 Projektialueet",
        )
        child_class = ProjectClass.objects.create(
            id=uuid.uuid4(),
            name="8 08 02 Kadut",
            parent=root_master,
            path="8 08 Projektialueet/8 08 02 Kadut",
        )
        sub_class = ProjectClass.objects.create(
            id=uuid.uuid4(),
            name="Lansisatama",
            parent=child_class,
            path="8 08 Projektialueet/8 08 02 Kadut/Lansisatama",
        )
        deep_sub_class = ProjectClass.objects.create(
            id=uuid.uuid4(),
            name="Hernesaari",
            parent=sub_class,
            path="8 08 Projektialueet/8 08 02 Kadut/Lansisatama/Hernesaari",
        )

        deep_project = Project.objects.create(
            name="Hernesaari katu",
            description="Deep hierarchy regression project",
            projectClass=deep_sub_class,
            programmed=True,
        )
        ProjectFinancial.objects.create(
            project=deep_project,
            year=year,
            value=100,
            forFrameView=False,
        )

        serializer = FinancialSumSerializer(
            context={
                "finance_year": year,
                "forcedToFrame": False,
                "for_coordinator": False,
                "frame_budgets": defaultdict(lambda: 0),
            }
        )

        master_total = serializer.get_finance_sums(root_master)["year0"]["plannedBudget"]
        class_total = serializer.get_finance_sums(child_class)["year0"]["plannedBudget"]

        self.assertEqual(class_total, 100)
        self.assertEqual(master_total, class_total)

