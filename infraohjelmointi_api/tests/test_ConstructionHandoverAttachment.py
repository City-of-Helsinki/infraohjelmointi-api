"""IO-857: construction handover attachment API tests.

Covers the cases the ticket lists: upload, list, download, delete, size limit and
MIME validation - plus the DRAFT-only rule and cross-handover isolation.
"""

import shutil
import tempfile
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from overrides import override
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from infraohjelmointi_api.models import (
    ConstructionHandover,
    ConstructionHandoverAttachment,
    Project,
    User,
)
from infraohjelmointi_api.views import BaseViewSet


# Tiny but structurally valid images, so fixtures look real to anything that
# sniffs magic bytes. The view trusts the multipart-declared content type rather
# than sniffing, but realistic fixtures keep the tests reusable.
JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xd9"
)
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfc\xff"
    b"\xff?\x00\x05\xfe\x02\xfe\xa3wL\x07\x00\x00\x00\x00IEND\xaeB`\x82"
)


# Per-class temp MEDIA_ROOT so uploaded fixtures never land in the repo.
@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ConstructionHandoverAttachmentTestCase(APITestCase):
    person_Id = uuid.UUID("66666666-6666-6666-6666-666666666666")

    @classmethod
    @override
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp_media = tempfile.mkdtemp(prefix="io857-test-media-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._tmp_media)
        cls._media_override.enable()

    @classmethod
    @override
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._tmp_media, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.person = User.objects.create(
            uuid=self.person_Id, first_name="Liisa", last_name="Virtanen"
        )
        self.project = Project.objects.create(
            name="IO-857 attachment test project",
            description="Project used for handover attachment tests",
        )
        self.handover = ConstructionHandover.objects.create(project=self.project)
        self.other_project = Project.objects.create(
            name="IO-857 other project", description="d"
        )
        self.other_handover = ConstructionHandover.objects.create(
            project=self.other_project
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _jpeg(self, name="suunnitelma.jpg"):
        return SimpleUploadedFile(name, JPEG_BYTES, content_type="image/jpeg")

    def _png(self, name="kustannusarvio.png"):
        return SimpleUploadedFile(name, PNG_BYTES, content_type="image/png")

    def _attachments_url(self, handover=None):
        return "/construction-handovers/{}/attachments/".format(
            (handover or self.handover).id
        )

    def _upload(self, *files, handover=None):
        return self.client.post(
            self._attachments_url(handover),
            data={"file": list(files)},
            format="multipart",
        )

    # ------------------------------------------------------------------
    # upload
    # ------------------------------------------------------------------

    def test_POST_attachment_returns_201_and_persists(self):
        response = self._upload(self._jpeg())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.json()), 1)

        row = ConstructionHandoverAttachment.objects.get()
        self.assertEqual(row.handover_id, self.handover.id)
        self.assertEqual(row.originalName, "suunnitelma.jpg")
        self.assertEqual(row.contentType, "image/jpeg")
        self.assertEqual(row.size, len(JPEG_BYTES))
        self.assertTrue(row.file.name.startswith("handover_attachments/"))

    def test_POST_accepts_png(self):
        response = self._upload(self._png())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ConstructionHandoverAttachment.objects.get().contentType, "image/png"
        )

    def test_POST_multiple_files_creates_a_row_each(self):
        response = self._upload(self._jpeg("a.jpg"), self._png("b.png"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 2)

    def test_POST_without_file_returns_400(self):
        response = self.client.post(
            self._attachments_url(), data={}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)

    def test_POST_records_uploader_when_authenticated(self):
        # force_authenticate rather than force_login: authentication_classes is
        # patched out for these tests, so a session alone leaves request.user
        # anonymous.
        self.client.force_authenticate(user=self.person)
        response = self._upload(self._jpeg())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ConstructionHandoverAttachment.objects.get().uploadedBy_id, self.person.uuid
        )

    # ------------------------------------------------------------------
    # validation: MIME + size
    # ------------------------------------------------------------------

    def test_POST_accepts_pdf(self):
        pdf = SimpleUploadedFile(
            "suunnitelma.pdf", b"%PDF-1.4 fake", content_type="application/pdf"
        )
        response = self._upload(pdf)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ConstructionHandoverAttachment.objects.get().contentType, "application/pdf"
        )

    def test_POST_rejects_unsupported_mime_type(self):
        bad = SimpleUploadedFile(
            "spreadsheet.xlsx", b"PK fake", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response = self._upload(bad)
        self.assertEqual(
            response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)

    @override_settings(HANDOVER_ATTACHMENT_MAX_BYTES=10)
    def test_POST_rejects_file_over_size_limit(self):
        response = self._upload(self._jpeg())
        self.assertEqual(
            response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)

    def test_POST_rejects_whole_batch_when_one_file_is_invalid(self):
        """A bad file mid-batch must not leave the good ones persisted."""
        bad = SimpleUploadedFile("x.txt", b"nope", content_type="text/plain")
        response = self._upload(self._jpeg("ok.jpg"), bad)
        self.assertEqual(
            response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------

    def test_GET_lists_attachments_for_the_handover_only(self):
        self._upload(self._jpeg("mine.jpg"))
        self._upload(self._png("theirs.png"), handover=self.other_handover)

        response = self.client.get(self._attachments_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["originalName"], "mine.jpg")
        self.assertIn("downloadUrl", body[0])

    def test_GET_returns_empty_list_when_no_attachments(self):
        response = self.client.get(self._attachments_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_handover_detail_embeds_attachments(self):
        self._upload(self._jpeg())
        response = self.client.get(
            "/construction-handovers/{}/".format(self.handover.id)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["attachments"]), 1)

    # ------------------------------------------------------------------
    # download
    # ------------------------------------------------------------------

    def test_GET_download_streams_the_file(self):
        self._upload(self._jpeg())
        row = ConstructionHandoverAttachment.objects.get()

        response = self.client.get(
            "/construction-handovers/{}/attachments/{}/download/".format(
                self.handover.id, row.id
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertIn("suunnitelma.jpg", response["Content-Disposition"])
        self.assertEqual(b"".join(response.streaming_content), JPEG_BYTES)

    def test_GET_download_is_scoped_to_its_handover(self):
        """An attachment id from another handover must not be readable here."""
        self._upload(self._png("theirs.png"), handover=self.other_handover)
        foreign = ConstructionHandoverAttachment.objects.get()

        response = self.client.get(
            "/construction-handovers/{}/attachments/{}/download/".format(
                self.handover.id, foreign.id
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_download_with_invalid_uuid_returns_400(self):
        response = self.client.get(
            "/construction-handovers/{}/attachments/not-a-uuid/download/".format(
                self.handover.id
            )
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------

    def test_DELETE_removes_row_and_file(self):
        self._upload(self._jpeg())
        row = ConstructionHandoverAttachment.objects.get()
        stored_path = row.file.path

        response = self.client.delete(
            "/construction-handovers/{}/attachments/{}/".format(
                self.handover.id, row.id
            )
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)

        import os

        self.assertFalse(os.path.exists(stored_path))

    def test_DELETE_unknown_attachment_returns_404(self):
        response = self.client.delete(
            "/construction-handovers/{}/attachments/{}/".format(
                self.handover.id, uuid.uuid4()
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleting_handover_cascades_to_attachments(self):
        self._upload(self._jpeg())
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 1)
        self.handover.delete()
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)

    # ------------------------------------------------------------------
    # DRAFT-only rule (same as financing rows)
    # ------------------------------------------------------------------

    def test_POST_is_rejected_when_handover_is_not_draft(self):
        self.handover.status = "SUBMITTED_TO_PROGRAMMER"
        self.handover.save()

        response = self._upload(self._jpeg())
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)

    def test_DELETE_is_rejected_when_handover_is_not_draft(self):
        self._upload(self._jpeg())
        row = ConstructionHandoverAttachment.objects.get()
        self.handover.status = "SUBMITTED_TO_CONSTRUCTION"
        self.handover.save()

        response = self.client.delete(
            "/construction-handovers/{}/attachments/{}/".format(
                self.handover.id, row.id
            )
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 1)

    def test_GET_and_download_still_work_when_handover_is_locked(self):
        """Locking blocks mutation, not reading."""
        self._upload(self._jpeg())
        row = ConstructionHandoverAttachment.objects.get()
        self.handover.status = "MOVED_TO_CONSTRUCTION_PREPARATION"
        self.handover.save()

        listing = self.client.get(self._attachments_url())
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listing.json()), 1)

        download = self.client.get(
            "/construction-handovers/{}/attachments/{}/download/".format(
                self.handover.id, row.id
            )
        )
        self.assertEqual(download.status_code, status.HTTP_200_OK)
