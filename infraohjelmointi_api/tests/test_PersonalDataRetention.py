import json
from datetime import date, timedelta
from io import StringIO

from dateutil.relativedelta import relativedelta
from django.core.management import call_command
from django.test import TestCase
from helusers.models import ADGroup
from rest_framework.test import APIClient

from infraohjelmointi_api.models import (
    AuditLog,
    ConstructionHandover,
    Person,
    Project,
    ProjectProgramme,
    ProjectProgrammeBasicInfo,
    ProjectProgrammer,
    Task,
    User,
)
from infraohjelmointi_api.services.PersonalDataRetentionService import (
    clear_personal_data,
    is_past_retention,
    overdue_projects,
    personal_data_summary,
)

ADMIN_GROUP = "sg_kymp_sso_io_admin"


def _years_ago(years: int, extra_days: int = 0) -> date:
    return date.today() - relativedelta(years=years) + timedelta(days=extra_days)


class PersonalDataRetentionFixtureMixin:
    def _make_person(self, first, last):
        return Person.objects.create(
            firstName=first, lastName=last, email=f"{last.lower()}@example.com",
            title="Title", phone="0401234567",
        )

    def _make_project(self, name, warranty_end, **links):
        return Project.objects.create(
            name=name, description="Test", estWarrantyPhaseEnd=warranty_end, **links
        )

    def _make_full_project(self, name, warranty_end):
        """Project with personal data in every category the retention job clears."""
        planner = self._make_person("Pekka", f"Planner{name}")
        construction = self._make_person("Kalle", f"Builder{name}")
        other = self._make_person("Olli", f"Other{name}")
        favourite = self._make_person("Fanny", f"Fav{name}")
        programmer = ProjectProgrammer.objects.create(firstName="Ada", lastName=f"Coder{name}")
        project = self._make_project(
            name, warranty_end,
            personPlanning=planner,
            personConstruction=construction,
            personProgramming=programmer,
        )
        project.otherPersons.add(other)
        project.favPersons.add(favourite)

        handover = ConstructionHandover.objects.create(
            project=project,
            personPlanning=planner,
            personFinancing=programmer,
            constructionProjectManager=construction,
        )
        handover.name = "Edited handover"
        handover.save()
        Task.objects.create(
            projectId=project, taskType="task", person=other,
            realizedCost=0, plannedCost=0, riskAssessment="",
        )
        programme = ProjectProgramme.objects.create(project=project)
        basic_info = ProjectProgrammeBasicInfo.objects.create(
            project_programme=programme,
            personsInvolved="Pekka Planner",
            projectProgrammeCompiler="Kalle Builder",
            inspector="Olli Other",
        )
        basic_info.summary = "Edited summary"
        basic_info.save()
        return project, {
            "planner": planner,
            "construction": construction,
            "other": other,
            "favourite": favourite,
            "programmer": programmer,
            "handover": handover,
        }


class PersonalDataRetentionServiceTests(PersonalDataRetentionFixtureMixin, TestCase):
    def test_overdue_lists_only_projects_past_five_years_with_personal_data(self):
        due, _ = self._make_full_project("Due", _years_ago(5, extra_days=-1))
        self._make_project("Not yet due", _years_ago(4))
        self._make_project("Due but empty", _years_ago(6))
        self._make_project("No warranty end", None)

        overdue_ids = [project.id for project, _ in overdue_projects()]

        self.assertEqual(overdue_ids, [due.id])

    def test_exactly_five_years_after_warranty_end_is_due(self):
        project, _ = self._make_full_project("Boundary", _years_ago(5))

        self.assertTrue(is_past_retention(project))
        self.assertIn(project.id, [p.id for p, _ in overdue_projects()])

    def test_one_day_before_five_years_is_not_due(self):
        project, _ = self._make_full_project("Almost", _years_ago(5, extra_days=1))

        self.assertFalse(is_past_retention(project))
        self.assertNotIn(project.id, [p.id for p, _ in overdue_projects()])

    def test_clear_removes_every_structured_personal_link(self):
        project, links = self._make_full_project("Full", _years_ago(6))

        result = clear_personal_data(project)

        project.refresh_from_db()
        self.assertIsNone(project.personPlanning)
        self.assertIsNone(project.personConstruction)
        self.assertIsNone(project.personProgramming)
        self.assertEqual(project.otherPersons.count(), 0)
        self.assertEqual(project.favPersons.count(), 0)

        links["handover"].refresh_from_db()
        self.assertIsNone(links["handover"].personPlanning)
        self.assertIsNone(links["handover"].personFinancing)
        self.assertIsNone(links["handover"].constructionProjectManager)
        self.assertFalse(Task.objects.filter(projectId=project, person__isnull=False).exists())

        basic_info = ProjectProgrammeBasicInfo.objects.get(project_programme__project=project)
        self.assertEqual(basic_info.personsInvolved, "")
        self.assertEqual(basic_info.projectProgrammeCompiler, "")
        self.assertEqual(basic_info.inspector, "")

        self.assertEqual(result["removed"]["projectPersons"], 4)
        self.assertEqual(result["removed"]["programmers"], 1)
        self.assertEqual(result["removed"]["handovers"], 1)
        self.assertEqual(result["removed"]["taskPersons"], 1)
        self.assertEqual(result["removed"]["programmeNames"], 1)
        self.assertEqual(personal_data_summary(project), {
            "projectPersons": 0,
            "programmers": 0,
            "handovers": 0,
            "taskPersons": 0,
            "programmeNames": 0,
        })

    def test_clear_scrubs_handover_and_programme_history(self):
        project, links = self._make_full_project("History", _years_ago(6))
        handover_history = ConstructionHandover.history.model.objects.filter(id=links["handover"].id)
        programme_history = ProjectProgrammeBasicInfo.history.model.objects.filter(
            project_programme__project=project
        )
        self.assertTrue(handover_history.exists())
        self.assertTrue(programme_history.exists())

        clear_personal_data(project)

        self.assertFalse(handover_history.filter(personPlanning__isnull=False).exists())
        self.assertFalse(handover_history.filter(constructionProjectManager__isnull=False).exists())
        self.assertFalse(programme_history.exclude(personsInvolved="").exists())
        self.assertFalse(programme_history.exclude(inspector="").exists())

    def test_clear_anonymizes_persons_no_longer_referenced(self):
        project, links = self._make_full_project("Anon", _years_ago(6))
        other_id = links["other"].id

        clear_personal_data(project)

        other = Person.objects.get(id=other_id)
        self.assertEqual(other.firstName, "")
        self.assertEqual(other.lastName, "")
        self.assertEqual(other.email, "")
        self.assertEqual(other.phone, "")
        self.assertEqual(other.title, "")
        self.assertTrue(other.deleted)

    def test_clear_keeps_person_still_used_by_newer_project(self):
        project, links = self._make_full_project("Shared", _years_ago(6))
        newer = self._make_project("Newer", date.today())
        Project.objects.filter(pk=newer.pk).update(personPlanning=links["planner"])

        clear_personal_data(project)

        planner = Person.objects.get(id=links["planner"].id)
        self.assertEqual(planner.firstName, "Pekka")
        self.assertFalse(planner.deleted)

    def test_clear_keeps_shared_programmer_lookup_row(self):
        project, links = self._make_full_project("Programmer", _years_ago(6))

        clear_personal_data(project)

        self.assertTrue(ProjectProgrammer.objects.filter(id=links["programmer"].id).exists())

    def test_clear_keeps_project_and_warranty_dates(self):
        warranty_end = _years_ago(6)
        project, _ = self._make_full_project("Keep", warranty_end)

        clear_personal_data(project)

        project.refresh_from_db()
        self.assertEqual(project.name, "Keep")
        self.assertEqual(project.estWarrantyPhaseEnd, warranty_end)


class PersonalDataRetentionApiTests(PersonalDataRetentionFixtureMixin, TestCase):
    def setUp(self):
        self.admin_group = ADGroup.objects.create(name=ADMIN_GROUP, display_name="admin")
        self.admin = User.objects.create_user(username="retention_admin", password="x")
        self.admin.ad_groups.add(self.admin_group)

        self.viewer = User.objects.create_user(username="retention_viewer", password="x")

        self.client = APIClient()

    def _list_url(self):
        return "/personal-data-retention/"

    def _confirm_url(self, project):
        return f"/personal-data-retention/{project.id}/confirm/"

    def test_list_forbidden_for_non_admin(self):
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get(self._list_url())

        self.assertEqual(response.status_code, 403)

    def test_list_returns_overdue_projects_with_counts_only(self):
        project, links = self._make_full_project("Listed", _years_ago(6))
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self._list_url())

        self.assertEqual(response.status_code, 200)
        entry = next(item for item in response.json() if item["projectId"] == str(project.id))
        self.assertEqual(entry["projectName"], "Listed")
        self.assertEqual(entry["personalData"]["projectPersons"], 4)
        self.assertNotIn(links["planner"].lastName, json.dumps(response.json()))

    def test_confirm_forbidden_for_non_admin_and_nothing_removed(self):
        project, links = self._make_full_project("Guarded", _years_ago(6))
        self.client.force_authenticate(user=self.viewer)

        response = self.client.post(self._confirm_url(project))

        self.assertEqual(response.status_code, 403)
        project.refresh_from_db()
        self.assertEqual(project.personPlanning_id, links["planner"].id)

    def test_confirm_rejects_project_not_yet_due(self):
        project, links = self._make_full_project("Early", _years_ago(4))
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(self._confirm_url(project))

        self.assertEqual(response.status_code, 400)
        project.refresh_from_db()
        self.assertEqual(project.personPlanning_id, links["planner"].id)

    def test_confirm_rejects_invalid_and_unknown_ids(self):
        self.client.force_authenticate(user=self.admin)

        self.assertEqual(self.client.post("/personal-data-retention/not-a-uuid/confirm/").status_code, 400)
        unknown = "6f1d3b0c-9d1e-4a6b-8f5e-2c7a9b1d4e5f"
        self.assertEqual(self.client.post(f"/personal-data-retention/{unknown}/confirm/").status_code, 404)

    def test_confirm_clears_project_and_audits_without_names(self):
        project, links = self._make_full_project("Confirmed", _years_ago(6))
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(self._confirm_url(project))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["removed"]["projectPersons"], 4)
        project.refresh_from_db()
        self.assertIsNone(project.personPlanning)

        audit = AuditLog.objects.get(project=project)
        self.assertEqual(audit.actor, self.admin)
        self.assertEqual(audit.origin, "infrahankkeiden_ohjelmointi")
        audit_text = json.dumps({"old": audit.old_values, "new": audit.new_values})
        for name in ("Planner", "Builder", "Other", "Fav", "Coder", "Pekka", "Kalle", "Olli"):
            self.assertNotIn(name, audit_text)

    def test_second_confirm_is_a_no_op_for_cleared_project(self):
        project, _ = self._make_full_project("Twice", _years_ago(6))
        self.client.force_authenticate(user=self.admin)
        self.client.post(self._confirm_url(project))

        response = self.client.post(self._confirm_url(project))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AuditLog.objects.filter(project=project).count(), 1)


class ReportPersonalDataRetentionCommandTests(PersonalDataRetentionFixtureMixin, TestCase):
    def test_reports_overdue_projects_and_deletes_nothing(self):
        project, links = self._make_full_project("Reported", _years_ago(6))
        out = StringIO()

        call_command("report_personal_data_retention", stdout=out)

        self.assertIn(str(project.id), out.getvalue())
        self.assertEqual(Person.objects.get(id=links["planner"].id).firstName, "Pekka")
        project.refresh_from_db()
        self.assertEqual(project.personPlanning_id, links["planner"].id)

    def test_reports_nothing_when_no_project_is_overdue(self):
        self._make_project("Fresh", _years_ago(1))
        out = StringIO()

        call_command("report_personal_data_retention", stdout=out)

        self.assertIn("No projects past personal data retention.", out.getvalue())
