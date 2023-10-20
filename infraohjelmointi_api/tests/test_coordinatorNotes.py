import uuid
from django.test import TestCase

from ..models import (
    CoordinatorNote,
    ProjectClass,
    User,
)

from ..serializers import CoordinatorNoteSerializer
from rest_framework.renderers import JSONRenderer
from overrides import override

from infraohjelmointi_api.views import BaseViewSet
from unittest.mock import patch

@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class CoordinatorNoteTestCase(TestCase):
    coordinatorClassName = "Test Master Class"
    coordinatorNote = "This is a test note!"
    updatedByFirstName = "John"
    updatedByLastName = "Doe"
    year = 2023
    createdDate = "2023-10-10T07:27:55.636353+03:00"
    updatedDate = "2023-10-10T07:27:55.636361+03:00"

    user_id = uuid.UUID("2c6dece3-cf93-45ba-867d-8f1dd14923fc")
    projectClass_Id = uuid.UUID("5f65a339-b3c9-48ee-a9b9-cb177546c253")
    note_id1 = "395941a7-c0ff-4bff-a65e-18634a0d16b8"
    note_id2 = "0277866c-cd15-4984-a25d-686d3c6d2131"

    @classmethod
    @override
    def setUpTestData(self):
        self.user = User.objects.create(
            uuid=self.user_id, first_name="John", last_name="Doe"
        )

        self.projectClass = ProjectClass.objects.create(
            id = self.projectClass_Id,
            name = self.coordinatorClassName,
            parent = None,
            path = self.coordinatorClassName,
        )

        CoordinatorNote.objects.create(
            id = self.note_id1,
            coordinatorClassName = self.coordinatorClassName,
            coordinatorClass = self.projectClass,
            coordinatorNote = self.coordinatorNote,
            year = self.year,
            createdDate = self.createdDate,
            updatedBy = self.user,
            updatedByFirstName = self.updatedByFirstName,
            updatedByLastName = self.updatedByLastName,
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
            coordinatorClass = self.projectClass,
            coordinatorNote = self.coordinatorNote,
            createdDate = self.createdDate,
            id = self.note_id2,
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

    def test_POST_coordinatorNote(self):
        data = {
            "coordinatorClass": self.projectClass_Id.__str__(),
            "coordinatorClassName": "Test Master Class",
            "coordinatorNote": "This is a test note!",
            "updatedBy": self.user_id.__str__(),
            "updatedByFirstName": "John",
            "updatedByLastName": "Doe",
            "year": 2023,
        }

        response = self.client.post(
            "/coordinator-notes/",
            data,
            content_type="application/json",
        )

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
   