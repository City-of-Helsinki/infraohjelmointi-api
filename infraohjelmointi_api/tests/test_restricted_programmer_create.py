"""Restricted programmers creating and moving items (IO-756).

Restricted programmers may create projects and notes only inside their
assigned classes, and must not move a project out of them. DRF runs no
object-level check on create, so these go through the real router and
permission stack rather than calling the permission class directly.
"""
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from helusers.models import ADGroup
from rest_framework.test import APIClient

from ..models import ClassProgrammerAssignment, Note, Project, ProjectClass, ProjectGroup

User = get_user_model()

PW_ON_CREATE = "infraohjelmointi_api.serializers.ProjectCreateSerializer.ProjectWiseService"


@patch(PW_ON_CREATE)
class RestrictedProgrammerCreateTestCase(TestCase):
    def setUp(self):
        self.own_class = ProjectClass.objects.create(
            name="B Siltojen peruskorjaus ja uusiminen",
            path="8 03 Kadut/8 03 01 Investoinnit/B Siltojen peruskorjaus ja uusiminen",
        )
        self.own_sub_class = ProjectClass.objects.create(
            name="Sillat alue 1",
            parent=self.own_class,
            path=f"{self.own_class.path}/Sillat alue 1",
        )
        self.other_class = ProjectClass.objects.create(
            name="B Lumenvastaanottopaikat ja hiekkasiilot",
            path="8 03 Kadut/8 03 01 Investoinnit/B Lumenvastaanottopaikat ja hiekkasiilot",
        )

        self.user = User.objects.create_user(
            username="teemu.testaaja@test.fi", email="teemu.testaaja@test.fi"
        )
        self.user.ad_groups.add(
            ADGroup.objects.create(
                name=settings.RESTRICTED_PROGRAMMER_AD_GROUP,
                display_name="Restricted programmers",
            )
        )
        ClassProgrammerAssignment.objects.create(
            user=self.user, project_class=self.own_class
        )

        self.own_project = Project.objects.create(
            name="Own project", description="d", projectClass=self.own_class
        )
        self.other_project = Project.objects.create(
            name="Other project", description="d", projectClass=self.other_class
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def _post_project(self, project_class):
        data = {"name": "New project", "description": "d"}
        if project_class is not None:
            data["projectClass"] = str(project_class.id)
        return self.client.post("/projects/", data, format="json")

    def test_can_create_project_in_assigned_class(self, _pw):
        response = self._post_project(self.own_class)
        self.assertEqual(response.status_code, 201, msg=response.content)

    def test_can_create_project_in_assigned_sub_class(self, _pw):
        response = self._post_project(self.own_sub_class)
        self.assertEqual(response.status_code, 201, msg=response.content)

    def test_cannot_create_project_in_other_class(self, _pw):
        response = self._post_project(self.other_class)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Project.objects.filter(name="New project").exists())

    def test_cannot_create_project_without_class(self, _pw):
        self.assertEqual(self._post_project(None).status_code, 403)

    def test_invalid_class_id_is_denied_not_a_server_error(self, _pw):
        response = self.client.post(
            "/projects/",
            {"name": "New project", "description": "d", "projectClass": "not-a-uuid"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_can_create_note_on_own_project(self, _pw):
        response = self.client.post(
            "/notes/",
            {"content": "x", "updatedBy": str(self.user.uuid), "project": str(self.own_project.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 201, msg=response.content)

    def test_cannot_create_note_on_other_project(self, _pw):
        response = self.client.post(
            "/notes/",
            {"content": "x", "updatedBy": str(self.user.uuid), "project": str(self.other_project.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Note.objects.filter(project=self.other_project).exists())

    def test_cannot_create_on_other_endpoints(self, _pw):
        for url, data in [
            ("/project-classes/", {"name": "New class", "path": "x"}),
            ("/project-groups/", {"name": "New group", "classRelation": str(self.own_class.id)}),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.post(url, data, format="json").status_code, 403)

    def test_can_move_project_within_assigned_classes(self, _pw):
        response = self.client.patch(
            f"/projects/{self.own_project.id}/",
            {"projectClass": str(self.own_sub_class.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 200, msg=response.content)

    def test_cannot_move_project_out_of_assigned_classes(self, _pw):
        response = self.client.patch(
            f"/projects/{self.own_project.id}/",
            {"projectClass": str(self.other_class.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.own_project.refresh_from_db()
        self.assertEqual(self.own_project.projectClass, self.own_class)

    def test_who_am_i_returns_group_and_class_paths(self, _pw):
        response = self.client.get("/who-am-i/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn(
            settings.RESTRICTED_PROGRAMMER_AD_GROUP,
            [group["name"] for group in body["ad_groups"]],
        )
        self.assertTrue(body["is_restricted_programmer"])
        self.assertEqual(body["restricted_class_paths"], [self.own_class.path])
        self.assertCountEqual(
            body["restricted_class_ids"],
            [str(self.own_class.id), str(self.own_sub_class.id)],
        )

    def test_who_am_i_flag_follows_configured_group_name(self, _pw):
        """The UI relies on the flag, so a renamed group must still be detected."""
        custom = User.objects.create_user(username="c@test.fi", email="c@test.fi")
        custom.ad_groups.add(ADGroup.objects.create(name="custom_restricted_group"))
        ClassProgrammerAssignment.objects.create(user=custom, project_class=self.own_class)
        self.client.force_authenticate(user=custom)

        with override_settings(RESTRICTED_PROGRAMMER_AD_GROUP="custom_restricted_group"):
            body = self.client.get("/who-am-i/").json()

        self.assertTrue(body["is_restricted_programmer"])
        self.assertIn("custom_restricted_group", [group["name"] for group in body["ad_groups"]])
        self.assertEqual(body["restricted_class_paths"], [self.own_class.path])

    def test_who_am_i_coordinator_in_group_is_not_restricted(self, _pw):
        self.user.ad_groups.add(ADGroup.objects.create(name="sg_kymp_sso_io_koordinaattorit"))

        body = self.client.get("/who-am-i/").json()

        self.assertFalse(body["is_restricted_programmer"])
        self.assertEqual(body["restricted_class_paths"], [])
        self.assertEqual(body["restricted_class_ids"], [])

    def test_who_am_i_class_paths_empty_for_other_users(self, _pw):
        other = User.objects.create_user(username="p@test.fi", email="p@test.fi")
        other.ad_groups.add(ADGroup.objects.create(name="sg_kymp_sso_io_ohjelmoijat"))
        ClassProgrammerAssignment.objects.create(user=other, project_class=self.own_class)
        self.client.force_authenticate(user=other)

        body = self.client.get("/who-am-i/").json()
        self.assertFalse(body["is_restricted_programmer"])
        self.assertEqual(body["restricted_class_paths"], [])
        self.assertEqual(body["restricted_class_ids"], [])

    # ------------------------------------------------------------------
    # Edits must not move anything out of the user's classes either
    # ------------------------------------------------------------------

    def _own_note(self):
        return Note.objects.create(content="x", project=self.own_project, updatedBy=self.user)

    def test_cannot_move_note_to_other_project(self, _pw):
        note = self._own_note()
        response = self.client.patch(
            f"/notes/{note.id}/", {"project": str(self.other_project.id)}, format="json"
        )
        self.assertEqual(response.status_code, 403)
        note.refresh_from_db()
        self.assertEqual(note.project, self.own_project)

    def test_can_edit_own_note(self, _pw):
        note = self._own_note()
        response = self.client.patch(f"/notes/{note.id}/", {"content": "y"}, format="json")
        self.assertEqual(response.status_code, 200, msg=response.content)

    def test_bulk_update_cannot_move_project_to_other_class(self, _pw):
        response = self.client.patch(
            "/projects/bulk-update/",
            [{"id": str(self.own_project.id), "data": {"projectClass": str(self.other_class.id)}}],
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.own_project.refresh_from_db()
        self.assertEqual(self.own_project.projectClass, self.own_class)

    def test_group_edit_cannot_move_group_or_pull_in_other_projects(self, _pw):
        group = ProjectGroup.objects.create(name="Group", classRelation=self.own_class)
        for data in [
            {"classRelation": str(self.other_class.id)},
            {"projects": [str(self.other_project.id)]},
        ]:
            with self.subTest(data=data):
                response = self.client.patch(f"/project-groups/{group.id}/", data, format="json")
                self.assertEqual(response.status_code, 403)
        self.other_project.refresh_from_db()
        self.assertIsNone(self.other_project.projectGroup)

    def test_json_array_body_is_denied_not_a_server_error(self, _pw):
        response = self.client.post("/projects/", [{"name": "x"}], format="json")
        self.assertEqual(response.status_code, 403)

    def test_can_read_history_of_other_project(self, _pw):
        response = self.client.get(f"/projects/{self.other_project.id}/history/")
        self.assertNotEqual(response.status_code, 403)

    def test_restricted_planner_cannot_create_project_programme(self, _pw):
        self.user.ad_groups.add(ADGroup.objects.create(name="sg_kymp_sso_io_ohjelmoijat"))
        response = self.client.post(
            "/project-programmes/", {"project": str(self.other_project.id)}, format="json"
        )
        self.assertEqual(response.status_code, 403)
