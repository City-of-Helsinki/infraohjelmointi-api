from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
import os
import shutil
import tempfile
import uuid
from ..models import Note, NoteImage, Project, ProjectType, User
from ..serializers import NoteGetSerializer, NoteHistorySerializer
from rest_framework.renderers import JSONRenderer
from overrides import override

from infraohjelmointi_api.views import BaseViewSet
from unittest.mock import patch


# IO-812: a tiny but valid JPEG (SOI + APP0 + EOI) so SimpleUploadedFile carries
# bytes that look like a real image to anything sniffing the first few bytes.
# (The view itself trusts the multipart-declared content_type rather than
# sniffing, but this keeps the fixtures realistic and reusable.)
JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xd9"
)
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfc\xff"
    b"\xff?\x00\x05\xfe\x02\xfe\xa3wL\x07\x00\x00\x00\x00IEND\xaeB`\x82"
)


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
            phaseDetail=None,
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


# IO-812: NoteImage upload / list / delete tests.
# Use a per-class temp MEDIA_ROOT so uploaded fixture files never end up in the
# repo. Test fixture mirrors NoteTestCase so we can hit `/notes/<id>/images/`.
@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class NoteImageTestCase(TestCase):
    note_Id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    other_note_Id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    person_Id = uuid.UUID("33333333-3333-3333-3333-333333333333")
    projectTypeId = uuid.UUID("44444444-4444-4444-4444-444444444444")
    projectId = uuid.UUID("55555555-5555-5555-5555-555555555555")

    @classmethod
    @override
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp_media = tempfile.mkdtemp(prefix="io812-test-media-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._tmp_media)
        cls._media_override.enable()

    @classmethod
    @override
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._tmp_media, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    @override
    def setUpTestData(cls):
        cls.projectType = ProjectType.objects.create(
            id=cls.projectTypeId, value="projectComplex"
        )
        cls.person = User.objects.create(
            uuid=cls.person_Id, first_name="Jane", last_name="Doe"
        )
        cls.project = Project.objects.create(
            id=cls.projectId,
            hkrId=43211,
            type=cls.projectType,
            name="IO-812 image test project",
            description="d",
            phase=None,
            programmed=True,
        )
        cls.note = Note.objects.create(
            id=cls.note_Id,
            content="Note with images",
            updatedBy=cls.person,
            project=cls.project,
        )
        cls.other_note = Note.objects.create(
            id=cls.other_note_Id,
            content="Unrelated note",
            updatedBy=cls.person,
            project=cls.project,
        )

    def _jpeg(self, name="kuva.jpg"):
        return SimpleUploadedFile(name, JPEG_BYTES, content_type="image/jpeg")

    def _png(self, name="kuva.png"):
        return SimpleUploadedFile(name, PNG_BYTES, content_type="image/png")

    def test_POST_image_returns_201_and_persists(self):
        response = self.client.post(
            "/notes/{}/images/".format(self.note_Id),
            {"file": self._jpeg()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, msg=response.content)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["fileName"], "kuva.jpg")
        self.assertEqual(body[0]["contentType"], "image/jpeg")
        self.assertEqual(body[0]["order"], 0)
        self.assertTrue(body[0]["url"].endswith(".jpg"))
        self.assertEqual(NoteImage.objects.filter(note_id=self.note_Id).count(), 1)

    def test_POST_multiple_images_assigns_incrementing_order(self):
        response = self.client.post(
            "/notes/{}/images/".format(self.note_Id),
            {"file": [self._jpeg("a.jpg"), self._png("b.png"), self._jpeg("c.jpg")]},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, msg=response.content)
        orders = [img["order"] for img in response.json()]
        self.assertEqual(orders, [0, 1, 2])

        # A second batch should continue numbering, not reset to 0.
        response2 = self.client.post(
            "/notes/{}/images/".format(self.note_Id),
            {"file": self._jpeg("d.jpg")},
            format="multipart",
        )
        self.assertEqual(response2.status_code, 201)
        self.assertEqual(response2.json()[0]["order"], 3)

    def test_GET_images_for_note(self):
        self.client.post(
            "/notes/{}/images/".format(self.note_Id),
            {"file": self._jpeg()},
            format="multipart",
        )
        response = self.client.get("/notes/{}/images/".format(self.note_Id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_GET_note_includes_images_array(self):
        self.client.post(
            "/notes/{}/images/".format(self.note_Id),
            {"file": self._jpeg()},
            format="multipart",
        )
        response = self.client.get("/notes/{}/".format(self.note_Id))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("images", body)
        self.assertEqual(len(body["images"]), 1)
        self.assertEqual(body["images"][0]["fileName"], "kuva.jpg")

    def test_DELETE_image_removes_row_and_file(self):
        post = self.client.post(
            "/notes/{}/images/".format(self.note_Id),
            {"file": self._jpeg()},
            format="multipart",
        )
        image_id = post.json()[0]["id"]
        on_disk = NoteImage.objects.get(id=image_id).file.path
        self.assertTrue(os.path.exists(on_disk))

        response = self.client.delete(
            "/notes/{}/images/{}/".format(self.note_Id, image_id)
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(NoteImage.objects.filter(id=image_id).exists())
        self.assertFalse(os.path.exists(on_disk))

    def test_POST_image_rejects_unsupported_content_type(self):
        bad = SimpleUploadedFile(
            "doc.pdf", b"%PDF-1.4 fake", content_type="application/pdf"
        )
        response = self.client.post(
            "/notes/{}/images/".format(self.note_Id),
            {"file": bad},
            format="multipart",
        )
        self.assertEqual(response.status_code, 415, msg=response.content)
        self.assertEqual(NoteImage.objects.filter(note_id=self.note_Id).count(), 0)

    @override_settings(NOTE_IMAGE_MAX_BYTES=10)
    def test_POST_image_rejects_oversized_file(self):
        response = self.client.post(
            "/notes/{}/images/".format(self.note_Id),
            {"file": self._jpeg()},  # JPEG_BYTES is well over 10 bytes
            format="multipart",
        )
        self.assertEqual(response.status_code, 413, msg=response.content)
        self.assertEqual(NoteImage.objects.filter(note_id=self.note_Id).count(), 0)

    def test_DELETE_image_404_when_note_mismatch(self):
        post = self.client.post(
            "/notes/{}/images/".format(self.note_Id),
            {"file": self._jpeg()},
            format="multipart",
        )
        image_id = post.json()[0]["id"]
        # Image belongs to self.note, not self.other_note -> must 404.
        response = self.client.delete(
            "/notes/{}/images/{}/".format(self.other_note_Id, image_id)
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(NoteImage.objects.filter(id=image_id).exists())

    def test_POST_image_requires_file_field(self):
        response = self.client.post(
            "/notes/{}/images/".format(self.note_Id), {}, format="multipart"
        )
        self.assertEqual(response.status_code, 400)

    def test_POST_batch_with_one_bad_file_writes_nothing(self):
        # Validation runs over the whole batch before any row/blob is written,
        # so a bad file in the middle must reject the entire request.
        bad = SimpleUploadedFile(
            "doc.pdf", b"%PDF-1.4 fake", content_type="application/pdf"
        )
        response = self.client.post(
            "/notes/{}/images/".format(self.note_Id),
            {"file": [self._jpeg("ok.jpg"), bad, self._png("also-ok.png")]},
            format="multipart",
        )
        self.assertEqual(response.status_code, 415, msg=response.content)
        self.assertEqual(NoteImage.objects.filter(note_id=self.note_Id).count(), 0)

    def test_GET_notes_list_does_not_n_plus_one_on_images(self):
        # Pin the image-prefetch contract by holding note count constant and
        # varying image count. With prefetch, adding more images to existing
        # notes must not increase the GET /notes/ query count - it's still
        # one bulk SELECT for all images regardless of how many there are.
        # (We deliberately don't compare across different note counts because
        # NoteGetSerializer.updatedBy has a separate, pre-existing N+1 on
        # User that is out of scope for IO-812.)
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as q_none:
            self.assertEqual(self.client.get("/notes/").status_code, 200)

        for name in ("a.jpg", "b.jpg", "c.jpg"):
            self.client.post(
                "/notes/{}/images/".format(self.note_Id),
                {"file": self._jpeg(name)},
                format="multipart",
            )
        self.client.post(
            "/notes/{}/images/".format(self.other_note_Id),
            {"file": self._jpeg("d.jpg")},
            format="multipart",
        )

        with CaptureQueriesContext(connection) as q_many:
            response = self.client.get("/notes/")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            len(q_many.captured_queries),
            len(q_none.captured_queries),
            msg=(
                "GET /notes/ query count grew with image count "
                f"({len(q_none.captured_queries)} -> "
                f"{len(q_many.captured_queries)}); image prefetch is missing."
            ),
        )
        by_id = {n["id"]: n for n in response.json()}
        self.assertEqual(len(by_id[str(self.note_Id)]["images"]), 3)
        self.assertEqual(len(by_id[str(self.other_note_Id)]["images"]), 1)
