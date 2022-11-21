from django.test import TestCase

from infraohjelmointi_api.models import Project, ProjectType
from ..models import Task
import uuid


class TaskTestCase(TestCase):
    TaskId = uuid.uuid4()

    @classmethod
    def setUpTestData(self):

        self.projectType = ProjectType.objects.create(
            id=uuid.uuid4(), value="projectComplex"
        )

        self.project = Project.objects.create(
            id=uuid.uuid4(),
            hkrId=uuid.uuid4(),
            sapProject=uuid.uuid4(),
            sapNetwork=uuid.uuid4(),
            type=self.projectType,
            name="Test project 1",
            description="description of the test project",
            phase="proposal",
            programmed=True,
            constructionPhaseDetail="Current phase is proposal",
            estPlanningStartYear=2022,
            estDesignEndYear=2023,
            estDesignStartDate="2022-11-20",
            estDesignEndDate="2022-11-28",
            contractPrepStartDate="2022-11-20",
            contractPrepEndDate="2022-11-20",
            warrantyStartDate="2022-11-20",
            warrantyExpireDate="2022-11-20",
            perfAmount=20000.00,
            unitCost=10000.00,
            costForecast=10000.00,
            neighborhood="my random neigbhorhood",
            comittedCost=120.0,
            tiedCurrYear=12000.00,
            realizedCost=20.00,
            spentCost=20000.00,
            riskAssess="Yes very risky test",
            priority="low",
            locked=True,
            comments="Comments random",
            delays="yes 1 delay because of tests",
        )

        self.Task = Task.objects.create(
            id=self.TaskId,
            projectId=self.project,
            hkrId=uuid.uuid4(),
            taskType="Very hard task",
            status="active",
            startDate="2022-11-20",
            endDate="2022-11-20",
            district="doe",
            need=5000.0,
        )

    def test_Task_is_created(self):

        self.assertEqual(
            Task.objects.filter(id=self.TaskId).exists(),
            True,
            msg="Created Task with Id {} does not exist in DB".format(self.TaskId),
        )
        Task = Task.objects.get(id=self.TaskId)
        self.assertIsInstance(Task, Task, msg="Object retrieved from DB != typeof Task")
        self.assertEqual(Task, self.Task, msg="Object from DB != created Object")

    def test_GET_all_Tasks(self):
        response = self.client.get("/budgets/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(len(response.json()), 1, msg="Number of returned Tasks != 1")
        Task.objects.create(
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
        self.assertEqual(len(response.json()), 2, msg="Number of returned Tasks != 2")

    def test_GET_one_Task(self):
        response = self.client.get("/budgets/{}/".format(self.TaskId))
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")

    def test_POST_Task(self):
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
            Task.objects.filter(id=new_createdId).exists(),
            True,
            msg="Project created using POST request does not exist in DB",
        )

    def test_PATCH_Task(self):
        data = {"site": "Helsinki Patched", "budgetMain": 5000}
        response = self.client.patch(
            "/budgets/{}/".format(self.TaskId),
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

    def test_DELETE_Task(self):
        response = self.client.delete("/budgets/{}/".format(self.TaskId))
        self.assertEqual(
            response.status_code,
            204,
            msg="Error deleting project with Id {}".format(self.TaskId),
        )
        self.assertEqual(
            Task.objects.filter(id=self.TaskId).exists(),
            False,
            msg="Project with Id {} still exists in DB".format(self.TaskId),
        )
