"""
Regression tests for IO-743 budget overlap fix.
Ensures the original IO-743 fix works correctly in both old and new methods.
"""

from datetime import date
from collections import defaultdict
from django.test import TestCase
from infraohjelmointi_api.models import ProjectClass, ClassFinancial
from infraohjelmointi_api.serializers import ProjectClassSerializer


class IO743RegressionTestCase(TestCase):
    """Regression tests for IO-743 false positive budget overlap warnings"""
    
    def setUp(self):
        """Set up the exact TSE-2028 scenario from IO-743"""
        self.year = date.today().year
        
        # Create the TSE-2028 hierarchy exactly as described in IO-743
        self.tse_2028 = ProjectClass.objects.create(
            name="TSE-2028 Parent",
            path="001",
            forCoordinatorOnly=True
        )
        
        self.child_class_1 = ProjectClass.objects.create(
            name="Child Class 1", 
            path="001.001",
            parent=self.tse_2028,
            forCoordinatorOnly=True
        )
        
        self.child_class_2 = ProjectClass.objects.create(
            name="Child Class 2",
            path="001.002", 
            parent=self.tse_2028,
            forCoordinatorOnly=True
        )
        
        # Create the exact budget scenario: 30,000 + 28,000 = 58,000
        self.create_financial_scenario(self.tse_2028, 58000, self.child_class_1, 30000, self.child_class_2, 28000)

    def create_financial_scenario(self, parent_class, parent_budget, child1_class, child1_budget, child2_class=None, child2_budget=0):
        """Helper method to create financial scenarios and reduce duplication"""
        ClassFinancial.objects.create(
            classRelation=parent_class,
            year=self.year,
            frameBudget=parent_budget,
            budgetChange=0
        )
        
        ClassFinancial.objects.create(
            classRelation=child1_class,
            year=self.year,
            frameBudget=child1_budget,
            budgetChange=0
        )
        
        if child2_class:
            ClassFinancial.objects.create(
                classRelation=child2_class,
                year=self.year,
                frameBudget=child2_budget,
                budgetChange=0
            )

    def test_tse_2028_scenario_old_method(self):
        """Test TSE-2028 scenario using old method (no frame_budgets context)"""
        # Use serializer without frame_budgets context (triggers old method)
        serializer = ProjectClassSerializer(
            [self.tse_2028],
            many=True,
            context={
                "for_coordinator": True,
                "finance_year": self.year,
                # No frame_budgets context - uses old method
            }
        )
        
        data = serializer.data[0]
        overlap_status = data['finances']['year0']['isFrameBudgetOverlap']
        
        # Should be False - children sum (58000) equals parent budget (58000)
        self.assertFalse(overlap_status, 
                        "TSE-2028 scenario should NOT show overlap warning (old method)")

    def test_tse_2028_scenario_new_method(self):
        """Test TSE-2028 scenario using new method (with frame_budgets context)"""
        # Create frame_budgets dict as used in coordinator view
        frame_budgets = defaultdict(lambda: 0)
        frame_budgets[f"{self.year}-{self.tse_2028.id}"] = 58000
        frame_budgets[f"{self.year}-{self.child_class_1.id}"] = 30000
        frame_budgets[f"{self.year}-{self.child_class_2.id}"] = 28000
        
        # Use serializer with frame_budgets context (triggers new method)
        serializer = ProjectClassSerializer(
            [self.tse_2028],
            many=True,
            context={
                "for_coordinator": True,
                "finance_year": self.year,
                "frame_budgets": frame_budgets
            }
        )
        
        data = serializer.data[0]
        overlap_status = data['finances']['year0']['isFrameBudgetOverlap']
        
        # Should be False - children sum (58000) equals parent budget (58000)
        self.assertFalse(overlap_status,
                        "TSE-2028 scenario should NOT show overlap warning (new method)")

    def test_methods_consistency_on_tse_2028(self):
        """Test that both methods give identical results for TSE-2028 scenario"""
        # Test old method
        old_method_serializer = ProjectClassSerializer(
            [self.tse_2028],
            many=True,
            context={
                "for_coordinator": True,
                "finance_year": self.year,
            }
        )
        old_method_result = old_method_serializer.data[0]['finances']['year0']['isFrameBudgetOverlap']
        
        # Test new method
        frame_budgets = defaultdict(lambda: 0)
        frame_budgets[f"{self.year}-{self.tse_2028.id}"] = 58000
        frame_budgets[f"{self.year}-{self.child_class_1.id}"] = 30000
        frame_budgets[f"{self.year}-{self.child_class_2.id}"] = 28000
        
        new_method_serializer = ProjectClassSerializer(
            [self.tse_2028],
            many=True,
            context={
                "for_coordinator": True,
                "finance_year": self.year,
                "frame_budgets": frame_budgets
            }
        )
        new_method_result = new_method_serializer.data[0]['finances']['year0']['isFrameBudgetOverlap']
        
        # Both methods must give the same result
        self.assertEqual(old_method_result, new_method_result,
                        "Old and new methods must give identical results for TSE-2028")
        self.assertFalse(old_method_result, "TSE-2028 should show no overlap (both methods)")

    def test_actual_overlap_scenario_both_methods(self):
        """Test a scenario that SHOULD trigger overlap in both methods"""
        # Create scenario where children exceed parent: 30,000 + 28,000 = 58,000 > 50,000
        overlap_parent = ProjectClass.objects.create(
            name="Overlap Parent",
            path="002",
            forCoordinatorOnly=True
        )
        
        overlap_child_1 = ProjectClass.objects.create(
            name="Overlap Child 1",
            path="002.001",
            parent=overlap_parent,
            forCoordinatorOnly=True
        )
        
        overlap_child_2 = ProjectClass.objects.create(
            name="Overlap Child 2",
            path="002.002",
            parent=overlap_parent,
            forCoordinatorOnly=True
        )
        
        # Parent budget is LESS than children sum
        self.create_financial_scenario(overlap_parent, 50000, overlap_child_1, 30000, overlap_child_2, 28000)
        
        # Test old method
        old_method_serializer = ProjectClassSerializer(
            [overlap_parent],
            many=True,
            context={
                "for_coordinator": True,
                "finance_year": self.year,
            }
        )
        old_method_result = old_method_serializer.data[0]['finances']['year0']['isFrameBudgetOverlap']
        
        # Test new method
        frame_budgets = defaultdict(lambda: 0)
        frame_budgets[f"{self.year}-{overlap_parent.id}"] = 50000
        frame_budgets[f"{self.year}-{overlap_child_1.id}"] = 30000
        frame_budgets[f"{self.year}-{overlap_child_2.id}"] = 28000
        
        new_method_serializer = ProjectClassSerializer(
            [overlap_parent],
            many=True,
            context={
                "for_coordinator": True,
                "finance_year": self.year,
                "frame_budgets": frame_budgets
            }
        )
        new_method_result = new_method_serializer.data[0]['finances']['year0']['isFrameBudgetOverlap']
        
        # Both should detect the overlap
        self.assertTrue(old_method_result, "Old method should detect overlap when children exceed parent")
        self.assertTrue(new_method_result, "New method should detect overlap when children exceed parent")
        self.assertEqual(old_method_result, new_method_result, "Both methods must agree on overlap detection")

    def test_no_children_scenario_both_methods(self):
        """Test scenario with no children (should never show overlap)"""
        no_children_parent = ProjectClass.objects.create(
            name="No Children Parent",
            path="003",
            forCoordinatorOnly=True
        )
        
        ClassFinancial.objects.create(
            classRelation=no_children_parent,
            year=self.year,
            frameBudget=100000,
            budgetChange=0
        )
        
        # Test old method
        old_method_serializer = ProjectClassSerializer(
            [no_children_parent],
            many=True,
            context={
                "for_coordinator": True,
                "finance_year": self.year,
            }
        )
        old_method_result = old_method_serializer.data[0]['finances']['year0']['isFrameBudgetOverlap']
        
        # Test new method
        frame_budgets = defaultdict(lambda: 0)
        frame_budgets[f"{self.year}-{no_children_parent.id}"] = 100000
        
        new_method_serializer = ProjectClassSerializer(
            [no_children_parent],
            many=True,
            context={
                "for_coordinator": True,
                "finance_year": self.year,
                "frame_budgets": frame_budgets
            }
        )
        new_method_result = new_method_serializer.data[0]['finances']['year0']['isFrameBudgetOverlap']
        
        # Neither should show overlap for parent with no children
        self.assertFalse(old_method_result, "Old method should not show overlap for parent with no children")
        self.assertFalse(new_method_result, "New method should not show overlap for parent with no children")
        self.assertEqual(old_method_result, new_method_result, "Both methods must agree on no-children scenario")

    def test_zero_parent_budget_scenario(self):
        """Test edge case where parent has zero budget but children have budgets"""
        zero_parent = ProjectClass.objects.create(
            name="Zero Budget Parent",
            path="004",
            forCoordinatorOnly=True
        )
        
        zero_child = ProjectClass.objects.create(
            name="Zero Budget Child",
            path="004.001",
            parent=zero_parent,
            forCoordinatorOnly=True
        )
        
        # Parent has zero budget, child has positive budget
        self.create_financial_scenario(zero_parent, 0, zero_child, 1000)
        
        # Test old method
        old_method_serializer = ProjectClassSerializer(
            [zero_parent],
            many=True,
            context={
                "for_coordinator": True,
                "finance_year": self.year,
            }
        )
        old_method_result = old_method_serializer.data[0]['finances']['year0']['isFrameBudgetOverlap']
        
        # Test new method
        frame_budgets = defaultdict(lambda: 0)
        frame_budgets[f"{self.year}-{zero_parent.id}"] = 0
        frame_budgets[f"{self.year}-{zero_child.id}"] = 1000
        
        new_method_serializer = ProjectClassSerializer(
            [zero_parent],
            many=True,
            context={
                "for_coordinator": True,
                "finance_year": self.year,
                "frame_budgets": frame_budgets
            }
        )
        new_method_result = new_method_serializer.data[0]['finances']['year0']['isFrameBudgetOverlap']
        
        # Both should detect overlap (1000 > 0)
        self.assertTrue(old_method_result, "Old method should detect overlap when child budget exceeds zero parent budget")
        self.assertTrue(new_method_result, "New method should detect overlap when child budget exceeds zero parent budget")
        self.assertEqual(old_method_result, new_method_result, "Both methods must agree on zero parent budget scenario")
