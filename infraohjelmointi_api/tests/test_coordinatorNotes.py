import uuid
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
    coordinatorNote = "This is a test note!"
    updatedBy = "2"
    updatedByFirstName = "John"
    updatedByLastName = "Doe"
    year = 2023
    createdDate = "2023-10-10T07:27:55.636353+03:00"
    updatedDate = "2023-10-10T07:27:55.636361+03:00"

    user_id = uuid.UUID("2c6dece3-cf93-45ba-867d-8f1dd14923fc")
    test_id1 = "395941a7-c0ff-4bff-a65e-18634a0d16b8"
    test_id2 = "0277866c-cd15-4984-a25d-686d3c6d2131"

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

    def test_GET_all_coordinatorNotes(self):
        response = self.client.get("/coordinator-notes/")
        notecount = CoordinatorNote.objects.all().count()
        self.assertEqual(response.status_code, 200, msg="Status code != 200")
        self.assertEqual(
            len(response.json()),
            notecount,
            msg="Number of retrieved Notes is != {}".format(notecount),
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
            notecount + 1,
            msg="Number of retrieved Notes is != {}".format(notecount),
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
            "coordinatorClass": "d94e8f20-3597-4430-8d29-7725ec26600f",
            "coordinatorClassName": "801 Esirakentaminen (kiinteä omaisuus)",
            "coordinatorNote": "This is a test note!",
            "updatedBy": self.user_id,
            "updatedByFirstName": "John",
            "updatedByLastName": "Doe",
            "year": 2023,
        }

        response = self.client.post(
            "/coordinator-notes/",
            data,
            content_type="application/json",
        )
        print("data values: ", data)
        print("post response: ", response, response.content)
        self.assertEqual(response.status_code, 201, msg="Status code != 201 , Error: {}".format(response.json()),)

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