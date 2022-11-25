from django.test import TestCase
from ..models import BudgetItem
import uuid
from rest_framework.renderers import JSONRenderer
from infraohjelmointi_api.serializers import BudgetItemSerializer


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
        # serialize the model instances
        serializer = BudgetItemSerializer(
            BudgetItem.objects.get(id=self.budgetItemId), many=False
        )

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected

        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(response.content, result_expected)

    def test_POST_budgetItem(self):
        data = {
            "budgetMain": 10000,
            "budgetPlan": 10000,
            "site": "Helsinki",
            "siteName": "Anankatu",
            "district": "doe",
            "need": 5000,
        }
        response = self.client.post("/budgets/", data, content_type="application/json")
        self.assertEqual(response.status_code, 201, msg="Status code != 201")
        new_createdId = response.json()["id"]
        self.assertEqual(
            BudgetItem.objects.filter(id=new_createdId).exists(),
            True,
            msg="Project created using POST request does not exist in DB",
        )

    def test_PATCH_budgetItem(self):
        data = {"site": "Helsinki Patched", "budgetMain": 5000}
        response = self.client.patch(
            "/budgets/{}/".format(self.budgetItemId),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["site"], data["site"], msg="Data not updated in the DB"
        )
        self.assertEqual(
            response.json()["budgetMain"],
            data["budgetMain"],
            msg="Data not updated in the DB",
        )

    def test_DELETE_budgetItem(self):
        response = self.client.delete("/budgets/{}/".format(self.budgetItemId))
        self.assertEqual(
            response.status_code,
            204,
            msg="Error deleting project with Id {}".format(self.budgetItemId),
        )
        self.assertEqual(
            BudgetItem.objects.filter(id=self.budgetItemId).exists(),
            False,
            msg="Project with Id {} still exists in DB".format(self.budgetItemId),
        )
