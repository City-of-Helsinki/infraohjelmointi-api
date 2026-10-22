from types import SimpleNamespace

from django.test import SimpleTestCase

from infraohjelmointi_api.services.ProjectPersonAuthorizationService import (
    ProjectPersonAuthorizationService,
)


class ProjectPersonAuthorizationServiceTestCase(SimpleTestCase):
    def setUp(self):
        self.auth_user = SimpleNamespace(
            is_authenticated=True,
            email="User@Example.com ",
        )
        self.unauth_user = SimpleNamespace(
            is_authenticated=False,
            email="user@example.com",
        )
        self.person_match = SimpleNamespace(email=" user@example.com")
        self.person_other = SimpleNamespace(email="other@example.com")

    def test_is_matching_project_person_email_returns_true_for_case_and_space_insensitive_match(self):
        result = ProjectPersonAuthorizationService.is_matching_project_person_email(
            user=self.auth_user,
            person=self.person_match,
        )

        self.assertTrue(result)

    def test_is_matching_project_person_email_returns_false_for_unauthenticated_user(self):
        result = ProjectPersonAuthorizationService.is_matching_project_person_email(
            user=self.unauth_user,
            person=self.person_match,
        )

        self.assertFalse(result)

    def test_is_matching_project_person_email_returns_false_for_non_matching_email(self):
        result = ProjectPersonAuthorizationService.is_matching_project_person_email(
            user=self.auth_user,
            person=self.person_other,
        )

        self.assertFalse(result)

    def test_is_person_planning_for_project_uses_project_person_planning(self):
        project = SimpleNamespace(personPlanning=self.person_match)

        result = ProjectPersonAuthorizationService.is_person_planning_for_project(
            user=self.auth_user,
            project=project,
        )

        self.assertTrue(result)

    def test_is_person_construction_for_project_uses_project_person_construction(self):
        project = SimpleNamespace(personConstruction=self.person_match)

        result = ProjectPersonAuthorizationService.is_person_construction_for_project(
            user=self.auth_user,
            project=project,
        )

        self.assertTrue(result)
