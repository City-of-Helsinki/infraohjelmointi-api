from datetime import date
from decimal import Decimal
from django.test import TestCase
from infraohjelmointi_api.models import (
    Project,
    ProjectPhase,
    ProjectCategory,
    ProjectType,
    ProjectFinancial,
)


class ProjectSignalTestCase(TestCase):
    def setUp(self):
        self.projectType, _ = ProjectType.objects.get_or_create(value="projectComplex")
        self.phase_proposal, _ = ProjectPhase.objects.get_or_create(value="proposal", defaults={"index": 1})
        self.phase_construction, _ = ProjectPhase.objects.get_or_create(value="construction", defaults={"index": 2})
        self.phase_other, _ = ProjectPhase.objects.get_or_create(value="planning", defaults={"index": 3})
        self.phase_suspended, _ = ProjectPhase.objects.get_or_create(value="suspended", defaults={"index": 10})
        self.category_k1, _ = ProjectCategory.objects.get_or_create(value="K1")
        self.category_k2, _ = ProjectCategory.objects.get_or_create(value="K2")

    def test_project_category_updates_to_k1_when_phase_changes_to_construction(self):
        # Create project in proposal phase
        project = Project.objects.create(
            name="Test Project",
            description="Description",
            type=self.projectType,
            phase=self.phase_proposal,
            category=self.category_k2
        )

        # Verify initial state
        self.assertEqual(project.phase, self.phase_proposal)
        self.assertEqual(project.category, self.category_k2)

        # Change phase to construction
        project.phase = self.phase_construction
        project.save()

        # Refresh from db
        project.refresh_from_db()

        # Verify category changed to K1
        self.assertEqual(project.phase, self.phase_construction)
        self.assertEqual(project.category, self.category_k1)

    def test_project_category_does_not_change_if_phase_is_not_construction(self):
        # Create project in proposal phase
        project = Project.objects.create(
            name="Test Project 2",
            description="Description",
            type=self.projectType,
            phase=self.phase_proposal,
            category=self.category_k2
        )

        # Change phase to something else than construction
        project.phase = self.phase_other
        project.save()

        # Refresh from db
        project.refresh_from_db()

        # Verify category did NOT change
        self.assertEqual(project.phase, self.phase_other)
        self.assertEqual(project.category, self.category_k2)

    def test_project_created_in_construction_phase_gets_k1(self):
        # Create project directly in construction phase
        project = Project.objects.create(
            name="Test Project 3",
            description="Description",
            type=self.projectType,
            phase=self.phase_construction,
            category=self.category_k2
        )

        # Refresh from db
        project.refresh_from_db()

        # If the signal works on creation too, it should be K1.
        # For now let's assume valid behavior is K1.
        self.assertEqual(project.category, self.category_k1)

    def test_project_category_does_not_change_when_updating_other_fields(self):
        # Create project in construction phase with K1
        project = Project.objects.create(
            name="Test Project 4",
            description="Description",
            type=self.projectType,
            phase=self.phase_construction,
            category=self.category_k1
        )

        # Change name. Category should remain K1.
        project.name = "Updated Name"
        project.save()
        project.refresh_from_db()
        self.assertEqual(project.category, self.category_k1)

    def test_suspended_date_and_from_phase_set_when_entering_suspended(self):
        project = Project.objects.create(
            name="Suspension Test",
            description="Description",
            type=self.projectType,
            phase=self.phase_proposal,
            category=self.category_k2,
        )
        self.assertIsNone(project.suspendedDate)
        self.assertIsNone(project.suspendedFromPhase_id)

        project.phase = self.phase_suspended
        project.save()
        project.refresh_from_db()

        self.assertEqual(project.phase, self.phase_suspended)
        self.assertEqual(project.suspendedDate, date.today())
        self.assertEqual(project.suspendedFromPhase, self.phase_proposal)

    def test_suspended_fields_cleared_when_leaving_suspended(self):
        project = Project.objects.create(
            name="Resume Test",
            description="Description",
            type=self.projectType,
            phase=self.phase_suspended,
            category=self.category_k2,
            suspendedDate=date.today(),
            suspendedFromPhase=self.phase_proposal,
        )
        project.refresh_from_db()
        self.assertEqual(project.suspendedFromPhase, self.phase_proposal)

        project.phase = self.phase_construction
        project.save()
        project.refresh_from_db()

        self.assertEqual(project.phase, self.phase_construction)
        self.assertIsNone(project.suspendedDate)
        self.assertIsNone(project.suspendedFromPhase)

    def test_suspended_date_set_when_created_directly_in_suspended(self):
        project = Project.objects.create(
            name="Created Suspended",
            description="Description",
            type=self.projectType,
            phase=self.phase_suspended,
            category=self.category_k2,
        )
        project.refresh_from_db()

        self.assertEqual(project.phase, self.phase_suspended)
        self.assertEqual(project.suspendedDate, date.today())
        self.assertIsNone(project.suspendedFromPhase)

    def test_suspended_fields_unchanged_when_phase_unchanged(self):
        project = Project.objects.create(
            name="No Change Test",
            description="Description",
            type=self.projectType,
            phase=self.phase_proposal,
            category=self.category_k2,
        )
        project.phase = self.phase_suspended
        project.save()
        project.refresh_from_db()
        saved_date = project.suspendedDate
        saved_from = project.suspendedFromPhase

        project.name = "Updated Name"
        project.save()
        project.refresh_from_db()

        self.assertEqual(project.suspendedDate, saved_date)
        self.assertEqual(project.suspendedFromPhase, saved_from)


class ReconcileFinancesOnScheduleChangeTestCase(TestCase):
    """The pre_save reconcile signal (IO-894) moves out-of-schedule budgets
    into the nearest in-schedule year whenever a project's planning /
    construction schedule changes.

    Baseline schedule for most tests: planning 2024-2025 + construction
    2026-2028, so the in-schedule years are {2024, 2025, 2026, 2027, 2028}.
    """

    def _create_project(
        self,
        *,
        name="Schedule project",
        planning_start_year=2024,
        est_planning_end=date(2025, 12, 31),
        est_construction_start=date(2026, 1, 1),
        construction_end_year=2028,
    ) -> Project:
        return Project.objects.create(
            name=name,
            description="-",
            planningStartYear=planning_start_year,
            estPlanningEnd=est_planning_end,
            estConstructionStart=est_construction_start,
            constructionEndYear=construction_end_year,
        )

    def _finance(self, project, *, year, value, for_frame_view=False):
        return ProjectFinancial.objects.create(
            project=project,
            year=year,
            value=Decimal(value),
            forFrameView=for_frame_view,
        )

    def _value_at(self, project, year, *, for_frame_view=False) -> Decimal:
        return ProjectFinancial.objects.get(
            project=project, year=year, forFrameView=for_frame_view
        ).value

    def test_no_schedule_change_leaves_existing_haamuluku_untouched(self):
        project = self._create_project()
        haamu = self._finance(project, year=2030, value="100.00")

        project.name = "Renamed"
        project.save()

        haamu.refresh_from_db()
        self.assertEqual(haamu.value, Decimal("100.00"))

    def test_planning_start_later_moves_money_to_new_start(self):
        project = self._create_project()
        orphan = self._finance(project, year=2024, value="500.00")

        project.planningStartYear = 2025
        project.save()

        orphan.refresh_from_db()
        self.assertEqual(orphan.value, Decimal("0"))
        self.assertEqual(self._value_at(project, 2025), Decimal("500.00"))

    def test_construction_end_earlier_moves_money_to_new_end(self):
        project = self._create_project()
        orphan = self._finance(project, year=2028, value="700.00")

        project.constructionEndYear = 2026
        project.save()

        orphan.refresh_from_db()
        self.assertEqual(orphan.value, Decimal("0"))
        self.assertEqual(self._value_at(project, 2026), Decimal("700.00"))

    def test_both_start_and_end_change_in_one_save(self):
        project = self._create_project()
        early = self._finance(project, year=2024, value="300.00")
        late = self._finance(project, year=2028, value="400.00")

        project.planningStartYear = 2025
        project.constructionEndYear = 2027
        project.save()

        early.refresh_from_db()
        late.refresh_from_db()
        self.assertEqual(early.value, Decimal("0"))
        self.assertEqual(late.value, Decimal("0"))
        self.assertEqual(self._value_at(project, 2025), Decimal("300.00"))
        self.assertEqual(self._value_at(project, 2027), Decimal("400.00"))

    def test_schedule_loosening_without_orphans_moves_nothing(self):
        project = self._create_project()
        in_schedule = self._finance(project, year=2026, value="100.00")

        project.constructionEndYear = 2030
        project.save()

        in_schedule.refresh_from_db()
        self.assertEqual(in_schedule.value, Decimal("100.00"))
        self.assertEqual(
            ProjectFinancial.objects.filter(project=project)
            .exclude(value=0)
            .count(),
            1,
        )

    def test_form_invisible_past_row_is_rescued(self):
        """Reproduces the IO-826 gap: a row at a year the form's 11-year
        window cannot represent stays in the DB; tightening the schedule
        orphans it and the signal rescues it into the new start year."""
        project = self._create_project()
        stranded = self._finance(project, year=2020, value="160.00")

        project.planningStartYear = 2025
        project.save()

        stranded.refresh_from_db()
        self.assertEqual(stranded.value, Decimal("0"))
        self.assertEqual(self._value_at(project, 2025), Decimal("160.00"))

    def test_value_accumulates_into_existing_target_year(self):
        project = self._create_project()
        orphan = self._finance(project, year=2024, value="500.00")
        existing = self._finance(project, year=2025, value="200.00")

        project.planningStartYear = 2025
        project.save()

        orphan.refresh_from_db()
        existing.refresh_from_db()
        self.assertEqual(orphan.value, Decimal("0"))
        self.assertEqual(existing.value, Decimal("700.00"))

    def test_frame_view_row_is_not_touched(self):
        project = self._create_project()
        frame_orphan = self._finance(
            project, year=2024, value="123.00", for_frame_view=True
        )

        project.planningStartYear = 2025
        project.save()

        frame_orphan.refresh_from_db()
        self.assertEqual(frame_orphan.value, Decimal("123.00"))

    def test_zero_valued_orphan_is_ignored(self):
        project = self._create_project()
        self._finance(project, year=2024, value="0.00")

        project.planningStartYear = 2025
        project.save()

        # Nothing moved into the new start year, no row created there.
        self.assertFalse(
            ProjectFinancial.objects.filter(
                project=project, year=2025, forFrameView=False
            ).exists()
        )

    def test_null_schedule_field_after_change_is_noop(self):
        project = self._create_project()
        orphan = self._finance(project, year=2024, value="500.00")

        project.estPlanningEnd = None
        project.save()

        orphan.refresh_from_db()
        self.assertEqual(orphan.value, Decimal("500.00"))

    def test_fully_inverted_schedule_leaves_money_untouched(self):
        """If no in-schedule year exists at all, the signal refuses to
        destroy money and leaves the rows for manual review."""
        project = self._create_project()
        orphan = self._finance(project, year=2024, value="500.00")

        # Invert both phases: planning 2030->2029, construction 2032->2031.
        project.planningStartYear = 2030
        project.estPlanningEnd = date(2029, 12, 31)
        project.estConstructionStart = date(2032, 1, 1)
        project.constructionEndYear = 2031
        project.save()

        orphan.refresh_from_db()
        self.assertEqual(orphan.value, Decimal("500.00"))

    def test_updated_date_bumped_on_moved_row(self):
        project = self._create_project()
        orphan = self._finance(project, year=2024, value="500.00")
        original_updated = orphan.updatedDate

        project.planningStartYear = 2025
        project.save()

        orphan.refresh_from_db()
        self.assertGreater(orphan.updatedDate, original_updated)

    def test_null_valued_orphan_is_ignored(self):
        project = self._create_project()
        orphan = self._finance(project, year=2024, value="0")
        ProjectFinancial.objects.filter(pk=orphan.pk).update(value=None)

        project.planningStartYear = 2025
        project.save()

        self.assertFalse(
            ProjectFinancial.objects.filter(
                project=project, year=2025, forFrameView=False
            ).exists()
        )
