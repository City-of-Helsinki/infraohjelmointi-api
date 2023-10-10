from django.test import TestCase

from ..models import CoordinatorNote, User
from ..serializers import CoordinatorNoteSerializer
from rest_framework.renderers import JSONRenderer
from overrides import override

from infraohjelmointi_api.views import BaseViewSet
from unittest.mock import patch


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class CoordinatorNoteTestCase(TestCase):
    coordinatorClass = "d94e8f20-3597-4430-8d29-7725ec26600f"
    coordinatorClassName = "801 Esirakentaminen (kiinteä omaisuus)"
    coordinatorClassId = "d94e8f20-3597-4430-8d29-7725ec26600f"
    coordinatorNote = "This is a test note!"
    createdDate = "2023-10-10T07:27:55.636353+03:00"
    updatedByFirstName = "Jane"
    updatedByLastName = "Doe"
    updatedDate = "2023-10-10T07:27:55.636361+03:00"
    year = 2023
    test_id1 = "395941a7-c0ff-4bff-a65e-18634a0d16b8"
    test_id2 = "0277866c-cd15-4984-a25d-686d3c6d2131"
    user_id = "2c6dece3-cf93-45ba-867d-8f1dd14923fc"

    @classmethod
    @override
    def setUpTestData(self):
        self.user = User.objects.create(
            uuid=self.user_id, first_name="John", last_name="Doe"
        )

        self.coordinatorNote = CoordinatorNote.objects.create(
            coordinatorClassName = self.coordinatorClassName,
            coordinatorNote = self.coordinatorNote,
            createdDate = self.createdDate,
            id = self.test_id1,
            updatedBy = self.user,
            updatedByFirstName = self.updatedByFirstName,
            updatedByLastName = self.updatedByLastName,
            year = self.year
        )
    """
    def test_note_is_created(self):
        self.assertTrue(
            CoordinatorNote.objects.filter(id=self.test_id1).exists(),
            msg="Object does not exist in DB",
        )
        coordinatorNote = CoordinatorNote.objects.get(id=self.test_id1)
        print("note!: ", coordinatorNote)
        print("self note!: ", self.coordinatorNote)
        self.assertIsInstance(
            coordinatorNote, CoordinatorNote, msg="Object retrieved from DB != typeof coordinatorNote Model"
        )
        self.assertEqual(coordinatorNote, self.coordinatorNote, msg="Object from DB != created Object")
    """

    def test_GET_all_coordinatorNotes(self):
        response = self.client.get("/coordinator-notes/")
        noteCount = CoordinatorNote.objects.all().count()
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            len(response.json()),
            noteCount,
            msg="Number of retrieved Notes is != {}".format(noteCount),
        )
        CoordinatorNote.objects.create(
            coordinatorClassName = self.coordinatorClassName,
            coordinatorNote = self.coordinatorNote,
            createdDate = self.createdDate,
            id = self.test_id2,
            updatedBy = self.user,
            updatedByFirstName = self.updatedByFirstName,
            updatedByLastName = self.updatedByLastName,
            updatedDate = self.updatedDate,
            year = self.year
        )
        response = self.client.get("/coordinator-notes/")
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            len(response.json()),
            noteCount + 1,
            msg="Number of retrieved Notes is != {}".format(noteCount),
        )

        # serialize the model instances
        serializer = CoordinatorNoteSerializer(CoordinatorNote.objects.all(), many=True)

        # convert the serialized data to JSON
        result_expected = JSONRenderer().render(serializer.data)

        # compare the JSON data returned to what is expected
        self.assertEqual(
            response.content, result_expected, msg="Data returned != data in DB"
        )
    """
    def test_POST_coordinatorNote(self):
        data = {
            "coordinatorClass": self.coordinatorClass,
            "coordinatorClassName": self.coordinatorClassName,
            "coordinatorNote": self.coordinatorNote,
            "updatedBy": self.user,
            "updatedByFirstName": self.updatedByFirstName,
            "updatedByLastName": self.updatedByLastName,
            "year": self.year
        }

        response = self.client.post(
            "/coordinator-notes/",
            data.values(),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, msg="Status code != 201")

        res_data = response.json()
        new_createdId = res_data["id"]
        
        del res_data["id"]
        del res_data["createdDate"]
        
        self.assertEqual(
            CoordinatorNote.objects.filter(id=new_createdId).exists(),
            True,
            msg="Note created using POST request does not exist in DB",
        )
    """