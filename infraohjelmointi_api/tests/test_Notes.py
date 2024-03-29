from django.test import TestCase
import uuid
from ..models import Project, ProjectType, User
from ..models import Note
from ..serializers import NoteGetSerializer, NoteHistorySerializer
from rest_framework.renderers import JSONRenderer
from overrides import override

from infraohjelmointi_api.views import BaseViewSet
from unittest.mock import patch


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class NoteTestCase(TestCase):
    note_1_Id = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    note_2_Id = uuid.UUID("da4a46f1-2939-43e2-8f92-40e94417813b")
    person_1_Id = uuid.UUID("2c6dece3-cf93-45ba-867d-8f1dd14923fc")
    projectTypeId = uuid.UUID("61ddbe61-e013-4bee-abf7-853d389f2b90")
    projectId = uuid.UUID("5d82c31b-4dee-4e48-be7c-b417e6c5bb9e")
    sapNetworkIds_1 = [uuid.UUID("1495aaf7-b0af-4847-a73b-7650145a73dc").__str__()]
    sapProjectId = "2814I00708"

    @classmethod
    @override
    def setUpTestData(self):
        self.projectType = ProjectType.objects.create(
            id=self.projectTypeId, value="projectComplex"
        )

        self.person_1 = User.objects.create(
            uuid=self.person_1_Id, first_name="John", last_name="Doe"
        )
        self.project = Project.objects.create(
            id=self.projectId,
            hkrId=43210,
            sapProject=self.sapProjectId,
            sapNetwork=self.sapNetworkIds_1,
            type=self.projectType,
            name="Test project 1",
            description="description of the test project",
            phase=None,
            programmed=True,
            constructionPhaseDetail=None,
            category=None,
            estPlanningStart="2022-11-20",
            estPlanningEnd="2022-11-30",
            estConstructionStart="2022-11-20",
            estConstructionEnd="2022-11-28",
            presenceStart="2022-11-20",
            presenceEnd="2022-11-20",
            visibilityStart="2022-11-20",
            visibilityEnd="2022-11-20",
            perfAmount=20000.00,
            unitCost=10000.00,
            costForecast=10000.00,
            neighborhood="my random neigbhorhood",
            comittedCost=120.0,
            tiedCurrYear=12000.00,
            realizedCost=20.00,
            spentCost=20000.00,
            riskAssessment=None,
            priority=None,
            comments="Comments random",
            delays="yes 1 delay because of tests",
        )

        self.note = Note.objects.create(
            id=self.note_1_Id,
            content="Random Note",
            updatedBy=self.person_1,
            project=self.project,
        )

    def test_note_is_created(self):
        self.assertTrue(
            Note.objects.filter(id=self.note_1_Id).exists(),
            msg="Object does not exist in DB",
        )
        note = Note.objects.get(id=self.note_1_Id)
        self.assertIsInstance(
            note, Note, msg="Object retrieved from DB != typeof Note Model"
        )
        self.assertEqual(note, self.note, msg="Object from DB != created Object")

    def test_note_foreign_key_exists(self):
        self.assertDictEqual(
            self.person_1.note_set.all().values()[0],
            Note.objects.filter(id=self.note_1_Id).values()[0],
            msg="Person foreign key does not exist in Note with id {}".format(
                self.note_1_Id
            ),
        )
        self.assertDictEqual(
            self.project.note_set.all().values()[0],
            Note.objects.filter(id=self.note_1_Id).values()[0],
            msg="Project foreign key does not exist in Note with id {}".format(
                self.note_1_Id
            ),
        )

    def test_history_exists(self):
        note = Note.objects.get(id=self.note_1_Id)
        old_content = note.content
        new_content = "This is the new content"
        note.content = new_content
        note.save()

        self.assertEqual(
            note.history.last().instance.content,
            old_content,
            msg="Last Note instance in history doesn't contain the old content",
        )
        self.assertEqual(
            note.history.latest().content,
            old_content,
            msg="Latest Note instance in history doesn't contain the latest content",
        )

    def test_GET_all_notes(self):
        response = self.client.get("/notes/")
        noteCount = Note.objects.all().count()
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            len(response.json()),
            noteCount,
            msg="Number of retrieved Notes is != {}".format(noteCount),
        )
        Note.objects.create(
            id=self.note_2_Id,
            content="Random Note 2",
            updatedBy=self.person_1,
            project=self.project,
        )
        response = self.client.get("/notes/")
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            len(response.json()),
            noteCount + 1,
            msg="Number of retrieved Notes is != {}".format(noteCount),
        )

        # serialize the model instances
        serializer = NoteGetSerializer(Note.objects.all(), many=True)

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected
        self.assertEqual(
            response.content, result_expected, msg="Data returned != data in DB"
        )

    def test_GET_history(self):
        response = self.client.get("/notes/{}/history/".format(self.note_1_Id))
        self.assertEqual(response.status_code, 200, msg="Status code != 200")

        serializer = NoteHistorySerializer(
            Note.objects.get(id=self.note_1_Id).history.all(), many=True
        )

        self.assertEqual(
            len(response.json()),
            len(serializer.data),
            msg="Data returned != data in DB",
        )

    def test_GET_history_by_user(self):
        response = self.client.get(
            "/notes/{}/history/{}/".format(self.note_1_Id, self.person_1_Id)
        )
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        serializer = NoteHistorySerializer(
            Note.objects.get(id=self.note_1_Id).history.all(), many=True
        )

        self.assertEqual(
            len(response.json()),
            len(serializer.data),
            msg="Data returned != data in DB",
        )

    def test_GET_one_note(self):
        response = self.client.get("/notes/{}/".format(self.note_1_Id))
        self.assertEqual(response.status_code, 200, msg="Status code != 200")

        # serialize the model instances
        serializer = NoteGetSerializer(Note.objects.get(id=self.note_1_Id), many=False)

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected

        self.assertEqual(
            response.content, result_expected, msg="Data returned != data in DB"
        )

    def test_POST_note(self):
        data = {
            "content": "Random Note POST",
            "updatedBy": self.person_1_Id.__str__(),
            "project": self.projectId.__str__(),
        }
        response = self.client.post(
            "/notes/",
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, msg="Status code != 201")

        res_data = response.json()
        new_createdId = res_data["id"]
        del res_data["id"]
        del res_data["createdDate"]

        self.assertEqual(
            Note.objects.filter(id=new_createdId).exists(),
            True,
            msg="Note created using POST request does not exist in DB",
        )

    def test_PATCH_note(self):
        data = {"content": "Patch content to replace old"}
        response = self.client.patch(
            "/notes/{}/".format(self.note_1_Id),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            response.json()["content"],
            data["content"],
            msg="Data not updated in the DB",
        )

    def test_DELETE_note(self):
        response = self.client.delete("/notes/{}/".format(self.note_1_Id))
        self.assertEqual(
            response.status_code,
            200,
            msg="Error deleting Note with Id {}".format(self.note_1_Id),
        )
        self.assertEqual(
            response.json()["id"],
            self.note_1_Id.__str__(),
            msg="Deleted note Id was not returned in response",
        )
        self.assertEqual(
            Note.objects.get(id=self.note_1_Id).deleted,
            True,
            msg="Soft delete failed, deleted field != True",
        )
