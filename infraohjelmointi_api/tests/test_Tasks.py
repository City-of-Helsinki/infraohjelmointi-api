from django.test import TestCase
from rest_framework.renderers import JSONRenderer
from infraohjelmointi_api.models import Person, Project, ProjectType, TaskStatus
from infraohjelmointi_api.serializers import TaskSerializer
from ..models import Task
import uuid


class TaskTestCase(TestCase):
    TaskId = uuid.UUID("bbba45f2-b0d4-4297-b0e2-4e60f8fa8412")
    TaskId2 = uuid.UUID("be923535-0b96-4cb5-b357-5e62a145281f")
    person_1_Id = uuid.UUID("f2f17b71-2d9a-4ddc-ba88-948a172c7bde")
    projectTypeId = uuid.UUID("61ddbe61-e013-4bee-abf7-853d389f2b90")
    sapNetworkId = uuid.UUID("b7a5f932-2286-4b4a-a4a5-a7a6b6039248")
    sapProjectId = uuid.UUID("7a12962d-f23f-40d7-966b-ee5df57b567d")
    projectId = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    taskStatusId = uuid.UUID("f2f17b71-2d9a-4ddc-ba88-948a172c7bde")
    sapNetworkIds_1 = [uuid.UUID("1495aaf7-b0af-4847-a73b-7650145a73dc").__str__()]
    sapProjectIds_1 = [uuid.UUID("e6f0805c-0b20-4248-bfae-21cf6bfe744a").__str__()]

    @classmethod
    def setUpTestData(self):
        self.taskStatus = TaskStatus.objects.create(
            id=self.taskStatusId, value="active"
        )

        self.projectType = ProjectType.objects.create(
            id=self.projectTypeId, value="projectComplex"
        )
        self.person_1 = Person.objects.create(
            id=self.person_1_Id,
            firstName="John",
            lastName="Doe",
            email="random@random.com",
            title="Manager",
            phone="0414853275",
        )

        self.project = Project.objects.create(
            id=self.projectId,
            hkrId=43210,
            sapProject=self.sapProjectIds_1,
            sapNetwork=self.sapNetworkIds_1,
            type=self.projectType,
            name="Test project 1",
            description="description of the test project",
            phase=None,
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
            priority=None,
            locked=True,
            comments="Comments random",
            delays="yes 1 delay because of tests",
        )

        self.task = Task.objects.create(
            id=self.TaskId,
            projectId=self.project,
            hkrId=12342,
            taskType="Very hard task",
            status=self.taskStatus,
            startDate="2022-11-20",
            endDate="2022-11-20",
            person=self.person_1,
            realizedCost=10000,
            plannedCost=50000,
            riskAssess="Very risky indeed",
        )

    def test_Task_is_created(self):

        self.assertEqual(
            Task.objects.filter(id=self.TaskId).exists(),
            True,
            msg="Created Task with Id {} does not exist in DB".format(self.TaskId),
        )
        task = Task.objects.get(id=self.TaskId)
        self.assertIsInstance(task, Task, msg="Object retrieved from DB != typeof Task")
        self.assertEqual(task.id, self.task.id, msg="Object from DB != created Object")

    def test_foreign_keys_exist(self):
        self.assertDictEqual(
            self.project.task_set.all().values()[0],
            Task.objects.filter(id=self.TaskId).values()[0],
            msg="Project foreign key does not exist in Task with id {}".format(
                self.TaskId
            ),
        )
        self.assertDictEqual(
            self.person_1.task_set.all().values()[0],
            Task.objects.filter(id=self.TaskId).values()[0],
            msg="Person foreign key does not exist in Task with id {}".format(
                self.TaskId
            ),
        )

        self.assertDictEqual(
            self.taskStatus.task_set.all().values()[0],
            Task.objects.filter(id=self.TaskId).values()[0],
            msg="TaskStatus foreign key does not exist in Task with id {}".format(
                self.TaskId
            ),
        )

    def test_GET_all_Tasks(self):
        response = self.client.get("/tasks/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(len(response.json()), 1, msg="Number of returned Tasks != 1")
        Task.objects.create(
            id=self.TaskId2,
            projectId=self.project,
            hkrId=22763,
            taskType="Very hard task",
            status=None,
            startDate="2022-11-20",
            endDate="2022-11-20",
            person=self.person_1,
            realizedCost=10000,
            plannedCost=50000,
            riskAssess="Very risky indeed",
        )
        response = self.client.get("/tasks/")
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        self.assertEqual(len(response.json()), 2, msg="Number of returned Tasks != 2")

    def test_GET_one_Task(self):
        response = self.client.get("/tasks/{}/".format(self.TaskId))
        self.assertEqual(
            response.json()["taskType"],
            self.task.taskType,
            msg="Response doesn't match the object in DB",
        )
        self.assertEqual(response.status_code, 200, msg="Status Code != 200")
        # serialize the model instances
        serializer = TaskSerializer(Task.objects.get(id=self.TaskId), many=False)

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected

        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(response.content, result_expected)

    def test_POST_Task(self):
        data = {
            "id": self.TaskId,
            "projectId": self.project.id.__str__(),
            "hkrId": 27618,
            "taskType": "Very hard task 2",
            "status": self.taskStatus.id.__str__(),
            "startDate": "2022-11-20",
            "endDate": "2022-11-20",
            "person": None,
            "realizedCost": 10000,
            "plannedCost": 50000,
            "riskAssess": "Very risky indeed",
        }
        response = self.client.post("/tasks/", data, content_type="application/json")
        self.assertEqual(response.status_code, 201, msg="Status code != 201")
        new_createdId = response.json()["id"]
        self.assertEqual(
            Task.objects.filter(id=new_createdId).exists(),
            True,
            msg="Task created using POST request does not exist in DB",
        )

    def test_PATCH_Task(self):
        data = {
            "taskType": "Easy Task",
            "status": None,
        }
        response = self.client.patch(
            "/tasks/{}/".format(self.TaskId),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["taskType"],
            data["taskType"],
            msg="Data not updated in the DB",
        )
        self.assertEqual(
            response.json()["status"],
            data["status"],
            msg="Data not updated in the DB",
        )

    def test_DELETE_Task(self):
        response = self.client.delete("/tasks/{}/".format(self.TaskId))
        self.assertEqual(
            response.status_code,
            204,
            msg="Error deleting task with Id {}".format(self.TaskId),
        )
        self.assertEqual(
            Task.objects.filter(id=self.TaskId).exists(),
            False,
            msg="Task with Id {} still exists in DB".format(self.TaskId),
        )
