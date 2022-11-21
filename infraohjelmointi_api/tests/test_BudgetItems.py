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

    def test_GET_all_budgetItems(self):
        response = self.client.get("/budgets/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(
            len(response.json()), 1, msg="Number of returned BudgetItems != 1"
        )
        BudgetItem.objects.create(
            id=uuid.uuid4(),
            budgetMain=10000,
            budgetPlan=10000,
            site="Helsinki",
            siteName="Anankatu",
            district="doe",
            need=5000.0,
        )
        response = self.client.get("/budgets/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(
            len(response.json()), 2, msg="Number of returned BudgetItems != 2"
        )

    def test_GET_one_budgetItem(self):
        response = self.client.get("/budgets/{}/".format(self.budgetItemId))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
