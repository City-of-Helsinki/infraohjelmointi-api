from django.test import TestCase
from ..models import BudgetItem
import uuid


class BudgetItemTestCase(TestCase):
    budgetItemId = uuid.uuid4()

    @classmethod
    def setUpTestData(self):
        self.budgetItem = BudgetItem.objects.create(
            id=self.budgetItemId,
            budgetMain=10000,
            budgetPlan=10000,
            site="Helsinki",
            siteName="Anankatu",
            district="doe",
            need=5000.0,
        )

    def test_budgetItem_is_created(self):

        self.assertEqual(
            BudgetItem.objects.filter(id=self.budgetItemId).exists(),
            True,
            msg="Created BudgetItem with Id {} does not exist in DB".format(
                self.budgetItemId
            ),
        )
        budgetItem = BudgetItem.objects.get(id=self.budgetItemId)
        self.assertIsInstance(
            budgetItem, BudgetItem, msg="Object retrieved from DB != typeof BudgetItem"
        )
        self.assertEqual(
            budgetItem, self.budgetItem, msg="Object from DB != created Object"
        )
