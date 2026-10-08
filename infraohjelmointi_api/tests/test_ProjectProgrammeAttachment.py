"""IO-914 / IO-936: project programme section attachments and location map.

Covers upload, list, download and delete of section attachments, the location map's
set/replace/serve/delete cycle, validation, the DRAFT lock, scoping to the programme,
cleanup of stored files, and the real role permissions
(ProjectProgrammeAttachmentPermissionTestCase).
"""

import os
import shutil
import tempfile
import uuid

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import override_settings
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch

from infraohjelmointi_api.models import (
    Project,
    ProjectProgramme,
    ProjectProgrammeAttachment,
    ProjectProgrammeBasicInfo,
    ProjectProgrammeDesignCriteria,
    ProjectProgrammeLocationMap,
    User,
)
from infraohjelmointi_api.views import BaseViewSet


JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xd9"
)
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfc\xff"
    b"\xff?\x00\x05\xfe\x02\xfe\xa3wL\x07\x00\x00\x00\x00IEND\xaeB`\x82"
)
PDF_BYTES = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n%%EOF\n"
# A .docx is a zip; the view does not sniff, so the zip magic is enough here.
DOCX_BYTES = b"PK\x03\x04" + b"\x00" * 26
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _jpeg(name="kuva.jpg"):
    return SimpleUploadedFile(name, JPEG_BYTES, content_type="image/jpeg")


def _png(name="kartta.png"):
    return SimpleUploadedFile(name, PNG_BYTES, content_type="image/png")


class _TempMediaMixin:
    """Per-class temp MEDIA_ROOT so uploaded fixtures never land in the repo."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp_media = tempfile.mkdtemp(prefix="io914-test-media-")
        cls._media_override = override_settings(MEDIA_ROOT=cls._tmp_media)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._tmp_media, ignore_errors=True)
        super().tearDownClass()

    def _stored_files(self):
        found = set()
        for root, _dirs, files in os.walk(self._tmp_media):
            found.update(os.path.join(root, f) for f in files)
        return found


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectProgrammeSectionAttachmentTestCase(_TempMediaMixin, APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="IO-914 project", description="d")
        self.programme = ProjectProgramme.objects.create(
            project=self.project, briefProjectProgramme=False
        )
        self.basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=self.programme
        )
        self.design_criteria = ProjectProgrammeDesignCriteria.objects.create(
            project_programme=self.programme
        )

        other_project = Project.objects.create(name="IO-914 other project", description="d")
        self.other_programme = ProjectProgramme.objects.create(project=other_project)
        self.other_basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=self.other_programme
        )

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _section_url(self, section_key="basic-info", programme=None):
        return "/project-programmes/{}/sections/{}/attachments/".format(
            (programme or self.programme).id, section_key
        )

    def _attachment_url(self, attachment_id, programme=None, suffix=""):
        return "/project-programmes/{}/attachments/{}/{}".format(
            (programme or self.programme).id, attachment_id, suffix
        )

    def _upload(self, *files, section_key="basic-info", programme=None):
        return self.client.post(
            self._section_url(section_key, programme),
            data={"file": list(files)},
            format="multipart",
        )

    # ------------------------------------------------------------------
    # upload
    # ------------------------------------------------------------------

    def test_POST_attachment_returns_201_and_persists_on_the_section(self):
        response = self._upload(_jpeg())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        row = ProjectProgrammeAttachment.objects.get()
        self.assertEqual(row.sectionObject, self.basic_info)
        self.assertEqual(row.originalName, "kuva.jpg")
        self.assertEqual(row.contentType, "image/jpeg")
        self.assertEqual(row.size, len(JPEG_BYTES))
        self.assertTrue(row.file.name.startswith("project_programme_attachments/"))
        # Relative API path, never a storage URL (which would carry the SAS token).
        self.assertEqual(
            response.json()[0]["downloadUrl"],
            "/project-programmes/{}/attachments/{}/download/".format(self.programme.id, row.id),
        )

    def test_POST_accepts_every_figma_type(self):
        """Figma: ".jpeg/.png/pdf/word, max 500 kb"; Word means .docx."""
        response = self._upload(
            _jpeg("a.jpeg"),
            _png("b.png"),
            SimpleUploadedFile("c.pdf", PDF_BYTES, content_type="application/pdf"),
            SimpleUploadedFile("d.docx", DOCX_BYTES, content_type=DOCX_TYPE),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertEqual(ProjectProgrammeAttachment.objects.count(), 4)

    def test_POST_section_key_accepts_any_separator_style(self):
        """Same key normalisation as the section transitions endpoint."""
        for key in ("design-criteria", "designCriteria", "design_criteria"):
            with self.subTest(key=key):
                response = self._upload(_jpeg(), section_key=key)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.design_criteria.attachments.count(), 3)

    def test_POST_rejects_legacy_word_documents(self):
        """.doc can carry macros and uploads are not virus scanned."""
        response = self._upload(
            SimpleUploadedFile("vanha.doc", b"\xd0\xcf\x11\xe0", content_type="application/msword")
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        self.assertIn("jpg, png, pdf, docx", response.json()["detail"])
        self.assertFalse(ProjectProgrammeAttachment.objects.exists())

    def test_POST_rejects_name_that_does_not_match_the_declared_type(self):
        response = self._upload(
            SimpleUploadedFile("x.html", PDF_BYTES, content_type="application/pdf")
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_POST_rejects_file_over_size_limit(self):
        with self.settings(PROJECT_PROGRAMME_ATTACHMENT_MAX_BYTES=len(JPEG_BYTES) - 1):
            response = self._upload(_jpeg())
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        self.assertFalse(ProjectProgrammeAttachment.objects.exists())

    def test_default_size_limit_matches_figma(self):
        from django.conf import settings

        self.assertEqual(settings.PROJECT_PROGRAMME_ATTACHMENT_MAX_BYTES, 500 * 1024)

    def test_POST_rejects_whole_batch_when_one_file_is_invalid(self):
        bad = SimpleUploadedFile("x.txt", b"nope", content_type="text/plain")
        response = self._upload(_jpeg(), bad)
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        self.assertFalse(ProjectProgrammeAttachment.objects.exists())

    def test_POST_without_file_returns_400(self):
        response = self.client.post(self._section_url(), data={}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_POST_to_unknown_section_key_returns_404(self):
        response = self._upload(_jpeg(), section_key="not-a-section")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_POST_to_a_section_that_does_not_exist_yet_returns_404(self):
        """Sections are created with POST /sections/<key>/ first, as for links."""
        response = self._upload(_jpeg(), section_key="maintenance-needs")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(ProjectProgrammeAttachment.objects.exists())

    def test_failed_batch_upload_leaves_no_files_behind(self):
        """Django writes each file to storage before its INSERT; if a later INSERT
        fails, every file already written must be removed with the rollback."""
        from django.db import IntegrityError
        from django.db.models.sql.compiler import SQLInsertCompiler

        real_as_sql = SQLInsertCompiler.as_sql
        calls = {"n": 0}

        def insert_then_fail(compiler, *args, **kwargs):
            sql = real_as_sql(compiler, *args, **kwargs)
            if compiler.query.model is ProjectProgrammeAttachment:
                calls["n"] += 1
                if calls["n"] == 2:
                    raise IntegrityError("simulated INSERT failure after the file was written")
            return sql

        before = self._stored_files()
        with patch.object(SQLInsertCompiler, "as_sql", autospec=True, side_effect=insert_then_fail):
            with self.assertRaises(IntegrityError):
                self._upload(_jpeg("one.jpg"), _png("two.png"))
        self.assertEqual(calls["n"], 2)
        self.assertFalse(ProjectProgrammeAttachment.objects.exists())
        self.assertEqual(self._stored_files(), before)

    # ------------------------------------------------------------------
    # list / embedding
    # ------------------------------------------------------------------

    def test_GET_lists_attachments_of_that_section_only(self):
        self._upload(_jpeg("perustiedot.jpg"))
        self._upload(_png("kriteerit.png"), section_key="design-criteria")
        self._upload(_png("muut.png"), programme=self.other_programme)

        response = self.client.get(self._section_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([a["originalName"] for a in response.json()], ["perustiedot.jpg"])

    def test_GET_unknown_section_returns_404(self):
        response = self.client.get(self._section_url("not-a-section"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_programme_GET_embeds_attachments_in_each_section(self):
        self._upload(_jpeg("perustiedot.jpg"))
        self._upload(_png("kriteerit.png"), section_key="design-criteria")

        body = self.client.get("/project-programmes/{}/".format(self.programme.id)).json()
        self.assertEqual(
            [a["originalName"] for a in body["basicInfo"]["attachments"]], ["perustiedot.jpg"]
        )
        self.assertEqual(
            [a["originalName"] for a in body["designCriteria"]["attachments"]],
            ["kriteerit.png"],
        )
        self.assertIsNone(body["locationMap"])

    def _attachment_query_count(self, url):
        table = ProjectProgrammeAttachment._meta.db_table
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        return sum(1 for q in queries.captured_queries if f'FROM "{table}"' in q["sql"])

    def test_programme_list_does_not_query_attachments_per_programme(self):
        """Without the prefetch every programme costs one attachments query per
        section, so vary the number of programmes. Only attachment queries are
        counted: section links still cost a query per section (pre-existing)."""
        self._upload(_jpeg())
        self._upload(_jpeg(), programme=self.other_programme)
        baseline = self._attachment_query_count("/project-programmes/")

        third = ProjectProgramme.objects.create(
            project=Project.objects.create(name="IO-914 third", description="d")
        )
        ProjectProgrammeBasicInfo.objects.create(project_programme=third)
        self._upload(_jpeg(), programme=third)
        self.assertEqual(self._attachment_query_count("/project-programmes/"), baseline)

    # ------------------------------------------------------------------
    # download
    # ------------------------------------------------------------------

    def test_GET_download_streams_the_file_as_an_attachment(self):
        self._upload(SimpleUploadedFile("selvitys.pdf", PDF_BYTES, content_type="application/pdf"))
        row = ProjectProgrammeAttachment.objects.get()

        response = self.client.get(self._attachment_url(row.id, suffix="download/"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn('attachment; filename="selvitys.pdf"', response["Content-Disposition"])
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(b"".join(response.streaming_content), PDF_BYTES)

    def test_GET_download_is_scoped_to_its_programme(self):
        """An attachment id from another programme must not be readable here."""
        self._upload(_png("theirs.png"), programme=self.other_programme)
        foreign = ProjectProgrammeAttachment.objects.get()

        response = self.client.get(self._attachment_url(foreign.id, suffix="download/"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_download_404_when_file_missing_from_storage(self):
        self._upload(_jpeg())
        row = ProjectProgrammeAttachment.objects.get()
        os.remove(row.file.path)

        response = self.client.get(self._attachment_url(row.id, suffix="download/"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_GET_download_with_invalid_uuid_returns_400(self):
        response = self.client.get(self._attachment_url("not-a-uuid", suffix="download/"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------

    def test_DELETE_removes_row_and_file(self):
        self._upload(_jpeg())
        row = ProjectProgrammeAttachment.objects.get()
        stored_path = row.file.path

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(self._attachment_url(row.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectProgrammeAttachment.objects.exists())
        self.assertFalse(os.path.exists(stored_path))

    def test_DELETE_unknown_attachment_returns_404(self):
        response = self.client.delete(self._attachment_url(uuid.uuid4()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_DELETE_is_scoped_to_its_programme(self):
        self._upload(_png("theirs.png"), programme=self.other_programme)
        foreign = ProjectProgrammeAttachment.objects.get()

        response = self.client.delete(self._attachment_url(foreign.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(ProjectProgrammeAttachment.objects.exists())

    def test_deleting_programme_cascades_to_attachments_and_their_files(self):
        """The generic FK alone would not cascade; the sections' GenericRelation
        does, and the post_delete signal then removes the files."""
        self._upload(_jpeg())
        self._upload(_png(), section_key="design-criteria")
        stored_paths = [a.file.path for a in ProjectProgrammeAttachment.objects.all()]

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete("/project-programmes/{}/".format(self.programme.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectProgrammeAttachment.objects.exists())
        for path in stored_paths:
            self.assertFalse(os.path.exists(path))

    # ------------------------------------------------------------------
    # DRAFT lock
    # ------------------------------------------------------------------

    def _lock(self, entity):
        entity.status = "COMPLETE"
        entity.save()

    def test_POST_is_rejected_when_programme_is_locked(self):
        self._lock(self.programme)
        response = self._upload(_jpeg())
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(ProjectProgrammeAttachment.objects.exists())

    def test_POST_is_rejected_when_section_is_locked(self):
        self._lock(self.basic_info)
        response = self._upload(_jpeg())
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        # Other sections are still editable.
        response = self._upload(_jpeg(), section_key="design-criteria")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_DELETE_is_rejected_when_programme_or_section_is_locked(self):
        self._upload(_jpeg())
        row = ProjectProgrammeAttachment.objects.get()
        for entity in (self.basic_info, self.programme):
            with self.subTest(locked=entity.__class__.__name__):
                self._lock(entity)
                response = self.client.delete(self._attachment_url(row.id))
                self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
                self.assertTrue(ProjectProgrammeAttachment.objects.exists())
                entity.status = "DRAFT"
                entity.save()

    def test_GET_and_download_still_work_when_locked(self):
        self._upload(_jpeg())
        row = ProjectProgrammeAttachment.objects.get()
        self._lock(self.programme)

        self.assertEqual(self.client.get(self._section_url()).status_code, status.HTTP_200_OK)
        download = self.client.get(self._attachment_url(row.id, suffix="download/"))
        self.assertEqual(download.status_code, status.HTTP_200_OK)


@patch.object(BaseViewSet, "authentication_classes", new=[])
@patch.object(BaseViewSet, "permission_classes", new=[])
class ProjectProgrammeLocationMapTestCase(_TempMediaMixin, APITestCase):
    def setUp(self):
        self.project = Project.objects.create(name="IO-936 project", description="d")
        self.programme = ProjectProgramme.objects.create(project=self.project)
        self.url = "/project-programmes/{}/location-map/".format(self.programme.id)
        # Map writes check programme edit rights in the view itself
        # (_assert_can_edit_or_complete), which the patched permissions do not skip.
        from helusers.models import ADGroup

        admin = User.objects.create_user(username="io936_admin", password="x")
        admin.ad_groups.add(ADGroup.objects.create(name="sg_kymp_sso_io_admin", display_name="a"))
        self.client.force_authenticate(user=admin)

    def _post(self, *files):
        return self.client.post(self.url, data={"file": list(files)}, format="multipart")

    def test_POST_sets_the_map_and_returns_201(self):
        response = self._post(_png())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)

        location_map = ProjectProgrammeLocationMap.objects.get()
        self.assertEqual(location_map.project_programme, self.programme)
        self.assertEqual(location_map.originalName, "kartta.png")
        self.assertTrue(location_map.file.name.startswith("project_programme_location_maps/"))
        self.assertEqual(response.json()["url"], self.url)

    def test_POST_replaces_the_previous_map_and_its_file(self):
        self._post(_png("vanha.png"))
        old_path = ProjectProgrammeLocationMap.objects.get().file.path

        with self.captureOnCommitCallbacks(execute=True):
            response = self._post(_jpeg("uusi.jpg"))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        self.assertEqual(ProjectProgrammeLocationMap.objects.get().originalName, "uusi.jpg")
        self.assertFalse(os.path.exists(old_path))

    def test_failed_replacement_keeps_the_previous_map(self):
        from django.db import IntegrityError
        from django.db.models.sql.compiler import SQLInsertCompiler

        self._post(_png("vanha.png"))
        old = ProjectProgrammeLocationMap.objects.get()
        files_before = self._stored_files()
        real_as_sql = SQLInsertCompiler.as_sql

        def fail_map_insert(compiler, *args, **kwargs):
            sql = real_as_sql(compiler, *args, **kwargs)
            if compiler.query.model is ProjectProgrammeLocationMap:
                raise IntegrityError("simulated INSERT failure after the file was written")
            return sql

        with self.captureOnCommitCallbacks(execute=True):
            with patch.object(SQLInsertCompiler, "as_sql", autospec=True, side_effect=fail_map_insert):
                with self.assertRaises(IntegrityError):
                    self._post(_jpeg("uusi.jpg"))
        self.assertEqual(ProjectProgrammeLocationMap.objects.get().pk, old.pk)
        self.assertTrue(os.path.exists(old.file.path))
        self.assertEqual(self._stored_files(), files_before)

    def test_POST_accepts_images_only(self):
        response = self._post(
            SimpleUploadedFile("kartta.pdf", PDF_BYTES, content_type="application/pdf")
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        self.assertFalse(ProjectProgrammeLocationMap.objects.exists())

    def test_POST_rejects_file_over_size_limit(self):
        with self.settings(PROJECT_PROGRAMME_LOCATION_MAP_MAX_BYTES=len(PNG_BYTES) - 1):
            response = self._post(_png())
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    def test_POST_requires_exactly_one_file(self):
        self.assertEqual(
            self.client.post(self.url, data={}, format="multipart").status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(self._post(_png("a.png"), _png("b.png")).status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(ProjectProgrammeLocationMap.objects.exists())

    def test_GET_serves_the_image_inline(self):
        self._post(_png())
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertNotIn("attachment", response.get("Content-Disposition", ""))
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(b"".join(response.streaming_content), PNG_BYTES)

    def test_GET_without_map_returns_404(self):
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_404_NOT_FOUND)

    def test_programme_GET_embeds_the_map(self):
        self._post(_png())
        body = self.client.get("/project-programmes/{}/".format(self.programme.id)).json()
        self.assertEqual(body["locationMap"]["originalName"], "kartta.png")
        self.assertEqual(body["locationMap"]["url"], self.url)

    def test_DELETE_removes_row_and_file(self):
        self._post(_png())
        stored_path = ProjectProgrammeLocationMap.objects.get().file.path

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectProgrammeLocationMap.objects.exists())
        self.assertFalse(os.path.exists(stored_path))

    def test_DELETE_without_map_returns_404(self):
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_404_NOT_FOUND)

    def test_POST_and_DELETE_are_rejected_when_programme_is_locked(self):
        self._post(_png())
        self.programme.status = "COMPLETE"
        self.programme.save()

        self.assertEqual(self._post(_jpeg()).status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(ProjectProgrammeLocationMap.objects.get().originalName, "kartta.png")
        # Reading still works.
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_200_OK)

    def test_completing_without_a_map_is_allowed(self):
        """Required-ness is a UI form rule, like the other required programme fields."""
        response = self.client.post(
            "/project-programmes/{}/transitions/".format(self.programme.id),
            {"to": "COMPLETE"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_deleting_programme_removes_the_map_file(self):
        self._post(_png())
        stored_path = ProjectProgrammeLocationMap.objects.get().file.path

        with self.captureOnCommitCallbacks(execute=True):
            self.programme.delete()
        self.assertFalse(os.path.exists(stored_path))


class ProjectProgrammeAttachmentPermissionTestCase(_TempMediaMixin, APITestCase):
    """The endpoints must pass the real permission classes: a missing allowlist entry
    is a 403 for real users that permission-patched tests cannot see (IO-812)."""

    def setUp(self):
        project = Project.objects.create(name="IO-914 permission project", description="d")
        self.programme = ProjectProgramme.objects.create(project=project)
        self.basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=self.programme
        )
        self.section_url = "/project-programmes/{}/sections/basic-info/attachments/".format(
            self.programme.id
        )
        self.map_url = "/project-programmes/{}/location-map/".format(self.programme.id)

    def _user_in_group(self, group_name):
        from helusers.models import ADGroup

        user = User.objects.create_user(username="io914_" + group_name, password="x")
        group, _ = ADGroup.objects.get_or_create(
            name=group_name, defaults={"display_name": group_name}
        )
        user.ad_groups.add(group)
        return user

    def _attachment_url(self, attachment_id, suffix=""):
        return "/project-programmes/{}/attachments/{}/{}".format(
            self.programme.id, attachment_id, suffix
        )

    def _seed(self):
        attachment = ProjectProgrammeAttachment.objects.create(
            sectionObject=self.basic_info,
            file=_jpeg(),
            originalName="kuva.jpg",
            contentType="image/jpeg",
            size=len(JPEG_BYTES),
        )
        ProjectProgrammeLocationMap.objects.create(
            project_programme=self.programme,
            file=_png(),
            originalName="kartta.png",
            contentType="image/png",
            size=len(PNG_BYTES),
        )
        return attachment

    def test_every_editing_role_can_upload_and_delete(self):
        from infraohjelmointi_api.permissions import (
            get_project_programme_contributor_group_name,
        )

        for group_name in (
            "sg_kymp_sso_io_koordinaattorit",  # IsCoordinator
            "sg_kymp_sso_io_ohjelmoijat",  # IsPlanner
            "sg_kymp_sso_io_projektipaallikot",  # IsProjectManager
            "sg_kymp_sso_io_admin",  # IsAdmin
            get_project_programme_contributor_group_name(),  # IsProjectProgrammeContributor
        ):
            with self.subTest(group=group_name):
                self.client.force_login(self._user_in_group(group_name))
                can_edit_programme = group_name != "sg_kymp_sso_io_projektipaallikot"

                upload = self.client.post(self.section_url, {"file": _jpeg()}, format="multipart")
                self.assertEqual(upload.status_code, status.HTTP_201_CREATED, upload.content)
                listing = self.client.get(self.section_url)
                self.assertEqual(listing.status_code, status.HTTP_200_OK)
                download = self.client.get(upload.json()[0]["downloadUrl"])
                self.assertEqual(download.status_code, status.HTTP_200_OK)
                delete = self.client.delete(self._attachment_url(upload.json()[0]["id"]))
                self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)

                if not can_edit_programme:
                    continue  # see test_commissioning_manager_cannot_change_the_location_map
                upload_map = self.client.post(self.map_url, {"file": _png()}, format="multipart")
                self.assertIn(upload_map.status_code, (200, 201), upload_map.content)
                self.assertEqual(self.client.get(self.map_url).status_code, status.HTTP_200_OK)
                delete_map = self.client.delete(self.map_url)
                self.assertEqual(delete_map.status_code, status.HTTP_204_NO_CONTENT)

    def test_commissioning_manager_cannot_change_the_location_map(self):
        """The map is programme-level content, so it follows programme PATCH rights:
        commissioning managers may only return a programme to DRAFT. They can still
        add section attachments, like they can edit sections and links."""
        self._seed()
        self.client.force_login(self._user_in_group("sg_kymp_sso_io_projektipaallikot"))

        self.assertEqual(self.client.get(self.map_url).status_code, status.HTTP_200_OK)
        upload_map = self.client.post(self.map_url, {"file": _png()}, format="multipart")
        self.assertEqual(upload_map.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.delete(self.map_url).status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ProjectProgrammeLocationMap.objects.get().originalName, "kartta.png")

    def test_read_only_roles_can_read_but_not_write(self):
        attachment = self._seed()
        for group_name in (
            "sl_dyn_kymp_sso_io_katselijat",  # IsViewer
            "sg_kymp_sso_io_rakennuttamisen_esihenkilot",  # IsConstructionManagementLead
        ):
            with self.subTest(group=group_name):
                self.client.force_login(self._user_in_group(group_name))

                self.assertEqual(self.client.get(self.section_url).status_code, status.HTTP_200_OK)
                download = self.client.get(self._attachment_url(attachment.id, "download/"))
                self.assertEqual(download.status_code, status.HTTP_200_OK)
                self.assertEqual(self.client.get(self.map_url).status_code, status.HTTP_200_OK)

                upload = self.client.post(self.section_url, {"file": _jpeg()}, format="multipart")
                self.assertEqual(upload.status_code, status.HTTP_403_FORBIDDEN)
                delete = self.client.delete(self._attachment_url(attachment.id))
                self.assertEqual(delete.status_code, status.HTTP_403_FORBIDDEN)
                upload_map = self.client.post(self.map_url, {"file": _png()}, format="multipart")
                self.assertEqual(upload_map.status_code, status.HTTP_403_FORBIDDEN)
                delete_map = self.client.delete(self.map_url)
                self.assertEqual(delete_map.status_code, status.HTTP_403_FORBIDDEN)

        self.assertEqual(ProjectProgrammeAttachment.objects.count(), 1)
        self.assertTrue(ProjectProgrammeLocationMap.objects.exists())

    def test_unauthenticated_user_is_rejected(self):
        attachment = self._seed()
        for response in (
            self.client.get(self.section_url),
            self.client.get(self._attachment_url(attachment.id, "download/")),
            self.client.get(self.map_url),
            self.client.post(self.section_url, {"file": _jpeg()}, format="multipart"),
            self.client.post(self.map_url, {"file": _png()}, format="multipart"),
        ):
            self.assertIn(response.status_code, (401, 403))
