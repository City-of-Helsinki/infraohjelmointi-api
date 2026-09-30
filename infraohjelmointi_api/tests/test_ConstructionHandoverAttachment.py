"""IO-857: construction handover attachment API tests.

Covers the cases the ticket lists: upload, list, download, delete, size limit and
MIME validation - plus the lock rule, cross-handover isolation, and the real
role permissions (ConstructionHandoverAttachmentPermissionTestCase).
"""

import os
import shutil
import tempfile
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
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

    def test_POST_rejects_pdf(self):
        """Figma allows only jpg/png; plans and cost estimates are links instead."""
        pdf = SimpleUploadedFile(
            "suunnitelma.pdf", b"%PDF-1.4 fake", content_type="application/pdf"
        )
        response = self._upload(pdf)
        self.assertEqual(
            response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)

    def test_default_size_limit_matches_figma(self):
        from django.conf import settings

        self.assertEqual(settings.HANDOVER_ATTACHMENT_MAX_BYTES, 500 * 1024)

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

    def test_POST_long_file_name_is_truncated_not_500(self):
        response = self._upload(self._jpeg("x" * 300 + ".jpg"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        stored = response.json()[0]["originalName"]
        self.assertEqual(len(stored), 255)
        self.assertTrue(stored.endswith(".jpg"))

    def test_failed_batch_upload_leaves_no_files_behind(self):
        """Each file is written to storage when its row is saved; if a later row in
        the batch fails, the rollback drops the rows and the files must go too."""
        real_create = ConstructionHandoverAttachment.objects.create
        calls = {"n": 0}

        def create_then_fail(**kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("simulated storage/DB failure")
            return real_create(**kwargs)

        def stored_files():
            found = set()
            for root, _dirs, files in os.walk(self._tmp_media):
                found.update(os.path.join(root, f) for f in files)
            return found

        before = stored_files()
        with patch.object(
            ConstructionHandoverAttachment.objects, "create", side_effect=create_then_fail
        ):
            with self.assertRaises(RuntimeError):
                self._upload(self._jpeg("one.jpg"), self._png("two.png"))
        self.assertEqual(calls["n"], 2)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)
        self.assertEqual(stored_files(), before)

    def test_project_handover_list_does_not_query_per_attachment(self):
        url = "/projects/{}/construction-handovers/".format(self.project.id)
        self._upload(self._jpeg("a.jpg"))
        with CaptureQueriesContext(connection) as one:
            self.assertEqual(self.client.get(url).status_code, status.HTTP_200_OK)
        self._upload(self._jpeg("b.jpg"), self._png("c.png"))
        with CaptureQueriesContext(connection) as three:
            response = self.client.get(url)
        self.assertEqual(len(response.json()[0]["attachments"]), 3)
        self.assertEqual(len(three.captured_queries), len(one.captured_queries))

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
        # Relative API path, never a storage URL (which would carry the SAS token).
        self.assertEqual(
            body[0]["downloadUrl"],
            "/construction-handovers/{}/attachments/{}/download/".format(
                self.handover.id, body[0]["id"]
            ),
        )

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
        self.assertIn('attachment; filename="suunnitelma.jpg"', response["Content-Disposition"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertIn("private", response["Cache-Control"])
        self.assertEqual(b"".join(response.streaming_content), JPEG_BYTES)

    def test_GET_download_404_when_file_missing_from_storage(self):
        self._upload(self._jpeg())
        row = ConstructionHandoverAttachment.objects.get()
        os.remove(row.file.path)

        response = self.client.get(
            "/construction-handovers/{}/attachments/{}/download/".format(
                self.handover.id, row.id
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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

        # The file is removed by the post_delete signal once the transaction commits.
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(
                "/construction-handovers/{}/attachments/{}/".format(
                    self.handover.id, row.id
                )
            )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)
        self.assertFalse(os.path.exists(stored_path))

    def test_DELETE_unknown_attachment_returns_404(self):
        response = self.client.delete(
            "/construction-handovers/{}/attachments/{}/".format(
                self.handover.id, uuid.uuid4()
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleting_handover_cascades_to_attachments_and_their_files(self):
        """Handovers can be deleted through the API in DRAFT/SUBMITTED_TO_PROGRAMMER;
        the CASCADE must not leave orphaned files in storage."""
        self._upload(self._jpeg())
        stored_path = ConstructionHandoverAttachment.objects.get().file.path

        with self.captureOnCommitCallbacks(execute=True):
            self.handover.delete()
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)
        self.assertFalse(os.path.exists(stored_path))

    def test_file_survives_a_rolled_back_delete(self):
        from django.db import transaction

        self._upload(self._jpeg())
        row = ConstructionHandoverAttachment.objects.get()
        stored_path = row.file.path

        class Rollback(Exception):
            pass

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            try:
                with transaction.atomic():
                    row.delete()
                    raise Rollback()
            except Rollback:
                pass
        self.assertEqual(callbacks, [])
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 1)
        self.assertTrue(os.path.exists(stored_path))

    # ------------------------------------------------------------------
    # Lock rule (same as financing rows): ConstructionHandover.is_locked
    # ------------------------------------------------------------------

    def test_POST_is_rejected_when_handover_is_locked(self):
        self.handover.status = "SUBMITTED_TO_CONSTRUCTION"
        self.handover.save()

        response = self._upload(self._jpeg())
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)

    def test_POST_is_allowed_when_submitted_to_programmer(self):
        """The programmer can still edit the handover, so attachments too."""
        self.handover.status = "SUBMITTED_TO_PROGRAMMER"
        self.handover.save()

        response = self._upload(self._jpeg())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 1)

    def test_DELETE_is_rejected_when_handover_is_locked(self):
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


class ConstructionHandoverAttachmentPermissionTestCase(APITestCase):
    """The attachment endpoints must pass the real permission classes, not just a
    patched-away check. IO-812 shipped a 403 for every real user because its actions
    were missing from the allowlists, and the patched tests could not see it."""

    @classmethod
    @override
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp_media = tempfile.mkdtemp(prefix="io857-perm-media-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._tmp_media)
        cls._media_override.enable()

    @classmethod
    @override
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._tmp_media, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        from helusers.models import ADGroup

        project = Project.objects.create(name="IO-857 permission project", description="d")
        self.handover = ConstructionHandover.objects.create(project=project)

        self.coordinator = User.objects.create_user(username="io857_coord", password="x")
        self.coordinator.ad_groups.add(
            ADGroup.objects.create(name="sg_kymp_sso_io_koordinaattorit", display_name="c")
        )
        self.lead = User.objects.create_user(username="io857_lead", password="x")
        self.lead.ad_groups.add(
            ADGroup.objects.create(
                name="sg_kymp_sso_io_rakennuttamisen_esihenkilot", display_name="l"
            )
        )

    def _url(self, suffix=""):
        return "/construction-handovers/{}/attachments/{}".format(self.handover.id, suffix)

    def _jpeg(self):
        return SimpleUploadedFile("perm.jpg", JPEG_BYTES, content_type="image/jpeg")

    def _seed_attachment(self):
        return ConstructionHandoverAttachment.objects.create(
            handover=self.handover,
            file=self._jpeg(),
            originalName="perm.jpg",
            contentType="image/jpeg",
            size=len(JPEG_BYTES),
        )

    def test_coordinator_can_upload_list_download_and_delete(self):
        self.client.force_login(self.coordinator)

        upload = self.client.post(self._url(), {"file": self._jpeg()}, format="multipart")
        self.assertEqual(upload.status_code, status.HTTP_201_CREATED, upload.content)
        attachment_id = upload.json()[0]["id"]

        listing = self.client.get(self._url())
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listing.json()), 1)

        download = self.client.get(listing.json()[0]["downloadUrl"])
        self.assertEqual(download.status_code, status.HTTP_200_OK)
        self.assertEqual(b"".join(download.streaming_content), JPEG_BYTES)

        delete = self.client.delete(self._url("{}/".format(attachment_id)))
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 0)

    def test_construction_management_lead_can_list_and_download(self):
        attachment = self._seed_attachment()
        self.client.force_login(self.lead)

        listing = self.client.get(self._url())
        self.assertEqual(listing.status_code, status.HTTP_200_OK, listing.content)
        download = self.client.get(self._url("{}/download/".format(attachment.id)))
        self.assertEqual(download.status_code, status.HTTP_200_OK)

    def test_construction_management_lead_cannot_upload_or_delete(self):
        """Leads' write rights are update/transition only."""
        attachment = self._seed_attachment()
        self.client.force_login(self.lead)

        upload = self.client.post(self._url(), {"file": self._jpeg()}, format="multipart")
        self.assertEqual(upload.status_code, status.HTTP_403_FORBIDDEN)
        delete = self.client.delete(self._url("{}/".format(attachment.id)))
        self.assertEqual(delete.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ConstructionHandoverAttachment.objects.count(), 1)

    def test_unauthenticated_user_is_rejected(self):
        attachment = self._seed_attachment()
        for response in (
            self.client.get(self._url()),
            self.client.get(self._url("{}/download/".format(attachment.id))),
            self.client.post(self._url(), {"file": self._jpeg()}, format="multipart"),
        ):
            self.assertIn(response.status_code, (401, 403))
