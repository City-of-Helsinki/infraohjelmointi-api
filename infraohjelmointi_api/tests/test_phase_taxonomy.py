"""IO-863: tests for the phase/detail taxonomy migration (0111_phase_taxonomy).

Layers:
1. Pure-function / constant-consistency tests (no DB).
2. Programming-phase backfill integration (drives op 1's callable).
3. End-state assertions on the real migrated DB (the restructure result).
4. Restructure-callable integration: setUp rebuilds the pre-restructure taxonomy
   by running the migration's reverse, then drives the forward callable against
   realistic project data.
"""

import importlib

from django.apps import apps as django_apps
from django.test import TestCase

from infraohjelmointi_api.models import (
    Person,
    Project,
    ProjectPhase,
    ProjectPhaseDetail,
    ProjectType,
)
from infraohjelmointi_api.services.utils.phase_taxonomy import (
    DELETED_PHASE_TO_DETAIL,
    DELETED_PHASE_VALUES,
    MOVED_DETAILS,
    NEW_DETAILS,
    PLANNING_PHASE_VALUE,
    PROGRAMMING_DETAIL_VALUE,
    REMOVED_CONSTRUCTION_DETAIL,
    SUSPENDED_DETAIL_VALUE,
    SUSPENDED_PHASE_VALUE,
    TARGET_PHASE_ORDER,
    WAITING_PLANNING_START_DETAIL_VALUE,
    WAITING_PROJECT_MANAGER_DETAIL_VALUE,
    decide_programming_phase_detail_value,
)

# Module name starts with a digit -> import via importlib to drive its callables.
taxonomy_migration = importlib.import_module(
    "infraohjelmointi_api.migrations.0111_phase_taxonomy"
)


class PhaseTaxonomyConstantsTests(TestCase):
    def test_deleted_phase_to_detail_is_inverse_of_moved_details(self):
        # The single most error-prone mapping: a swap silently mislabels every
        # migrated project. It must be exactly the inverse of MOVED_DETAILS.
        self.assertEqual(
            DELETED_PHASE_TO_DETAIL,
            {phase: detail for detail, phase in MOVED_DETAILS.items()},
        )

    def test_target_order_is_unique_and_excludes_deleted(self):
        self.assertEqual(len(TARGET_PHASE_ORDER), len(set(TARGET_PHASE_ORDER)))
        self.assertIn(PLANNING_PHASE_VALUE, TARGET_PHASE_ORDER)
        # IO-863: `suspended` is no longer a phase — it is a designPlanning detail.
        self.assertNotIn(SUSPENDED_PHASE_VALUE, TARGET_PHASE_ORDER)
        self.assertTrue(set(TARGET_PHASE_ORDER).isdisjoint(DELETED_PHASE_VALUES))


class DecideProgrammingPhaseDetailValueTests(TestCase):
    def test_planning_start_year_2027_assigns_programming(self):
        self.assertEqual(
            decide_programming_phase_detail_value(2027, has_planning_person=True),
            PROGRAMMING_DETAIL_VALUE,
        )
        self.assertEqual(
            decide_programming_phase_detail_value(2027, has_planning_person=False),
            PROGRAMMING_DETAIL_VALUE,
        )

    def test_planning_start_year_2030_assigns_programming(self):
        self.assertEqual(
            decide_programming_phase_detail_value(2030, has_planning_person=False),
            PROGRAMMING_DETAIL_VALUE,
        )

    def test_planning_start_year_2026_with_pm_assigns_waiting_planning_start(self):
        self.assertEqual(
            decide_programming_phase_detail_value(2026, has_planning_person=True),
            WAITING_PLANNING_START_DETAIL_VALUE,
        )

    def test_planning_start_year_2026_without_pm_assigns_waiting_project_manager(self):
        self.assertEqual(
            decide_programming_phase_detail_value(2026, has_planning_person=False),
            WAITING_PROJECT_MANAGER_DETAIL_VALUE,
        )

    def test_planning_start_year_2025_returns_none(self):
        self.assertIsNone(decide_programming_phase_detail_value(2025, has_planning_person=True))
        self.assertIsNone(decide_programming_phase_detail_value(2025, has_planning_person=False))

    def test_none_planning_start_year_assigns_programming(self):
        # IO-863 spec: ">= 2027 or empty (tai on tyhjä)" -> programming.
        self.assertEqual(
            decide_programming_phase_detail_value(None, has_planning_person=True),
            PROGRAMMING_DETAIL_VALUE,
        )
        self.assertEqual(
            decide_programming_phase_detail_value(None, has_planning_person=False),
            PROGRAMMING_DETAIL_VALUE,
        )


class ProgrammingBackfillIntegrationTests(TestCase):
    def setUp(self):
        self.project_type, _ = ProjectType.objects.get_or_create(value="projectComplex")
        self.programming_phase, _ = ProjectPhase.objects.get_or_create(
            value="programming", defaults={"index": 2}
        )
        self.proposal_phase, _ = ProjectPhase.objects.get_or_create(
            value="proposal", defaults={"index": 0}
        )
        self.waiting_pm_detail, _ = ProjectPhaseDetail.objects.get_or_create(
            value=WAITING_PROJECT_MANAGER_DETAIL_VALUE, projectPhase=self.programming_phase
        )
        self.waiting_planning_start_detail, _ = ProjectPhaseDetail.objects.get_or_create(
            value=WAITING_PLANNING_START_DETAIL_VALUE, projectPhase=self.programming_phase
        )
        # The migration already created the "programming" detail; remove it so the
        # backfill callable re-creates it (simulates pre-op-1 state).
        ProjectPhaseDetail.objects.filter(
            value=PROGRAMMING_DETAIL_VALUE, projectPhase=self.programming_phase
        ).delete()

        self.planner = Person.objects.create(
            firstName="Pia", lastName="Planner", email="pia@example.com",
            title="Project Manager", phone="000",
        )

    def _make_project(self, *, name, planning_start_year, planner=None, phase=None):
        return Project.objects.create(
            name=name, description=name, type=self.project_type,
            phase=phase or self.programming_phase,
            planningStartYear=planning_start_year, personPlanning=planner,
        )

    def test_backfill_assigns_correct_details(self):
        future_with_pm = self._make_project(name="future_with_pm", planning_start_year=2027, planner=self.planner)
        future_without_pm = self._make_project(name="future_without_pm", planning_start_year=2030)
        y2026_with_pm = self._make_project(name="2026_with_pm", planning_start_year=2026, planner=self.planner)
        y2026_without_pm = self._make_project(name="2026_without_pm", planning_start_year=2026)
        y2025 = self._make_project(name="2025", planning_start_year=2025, planner=self.planner)
        no_year = self._make_project(name="no_year", planning_start_year=None)
        other_phase = self._make_project(name="other_phase", planning_start_year=2027, phase=self.proposal_phase)

        taxonomy_migration.backfill_programming(django_apps, schema_editor=None)

        programming_detail = ProjectPhaseDetail.objects.get(
            value=PROGRAMMING_DETAIL_VALUE, projectPhase=self.programming_phase
        )
        for proj in (future_with_pm, future_without_pm, y2026_with_pm, y2026_without_pm, y2025, no_year, other_phase):
            proj.refresh_from_db()

        self.assertEqual(future_with_pm.phaseDetail, programming_detail)
        self.assertEqual(future_without_pm.phaseDetail, programming_detail)
        self.assertEqual(y2026_with_pm.phaseDetail, self.waiting_planning_start_detail)
        self.assertEqual(y2026_without_pm.phaseDetail, self.waiting_pm_detail)
        self.assertIsNone(y2025.phaseDetail)  # < 2026 left untouched
        self.assertEqual(no_year.phaseDetail, programming_detail)  # empty -> programming
        self.assertIsNone(other_phase.phaseDetail)  # non-programming phase untouched

    def test_backfill_is_idempotent(self):
        project = self._make_project(name="idempotent", planning_start_year=2027, planner=self.planner)
        taxonomy_migration.backfill_programming(django_apps, schema_editor=None)
        project.refresh_from_db()
        first = project.phaseDetail
        taxonomy_migration.backfill_programming(django_apps, schema_editor=None)
        project.refresh_from_db()
        self.assertEqual(project.phaseDetail, first)


class TaxonomyEndStateTests(TestCase):
    """Assert the real migrated DB shape (no manipulation in setUp)."""

    def test_planning_phase_holds_the_moved_details(self):
        planning = ProjectPhase.objects.get(value=PLANNING_PHASE_VALUE)
        # the moved planning details + the demoted `suspended` detail (IO-863)
        self.assertEqual(
            {d.value for d in planning.phaseDetails.all()},
            set(MOVED_DETAILS.keys()) | {SUSPENDED_DETAIL_VALUE},
        )

    def test_deleted_phases_and_removed_detail_are_gone(self):
        self.assertFalse(ProjectPhase.objects.filter(value__in=DELETED_PHASE_VALUES).exists())
        self.assertFalse(ProjectPhaseDetail.objects.filter(value=REMOVED_CONSTRUCTION_DETAIL).exists())

    def test_suspended_phase_removed_and_demoted_to_designplanning_detail(self):
        # IO-863: the standalone `suspended` phase is gone; "Keskeytetty toistaiseksi"
        # is now a phaseDetail under designPlanning.
        self.assertFalse(ProjectPhase.objects.filter(value=SUSPENDED_PHASE_VALUE).exists())
        planning = ProjectPhase.objects.get(value=PLANNING_PHASE_VALUE)
        self.assertTrue(planning.phaseDetails.filter(value=SUSPENDED_DETAIL_VALUE).exists())

    def test_new_details_present_under_right_phases(self):
        for phase_value, detail_values in NEW_DETAILS.items():
            present = {
                d.value for d in ProjectPhase.objects.get(value=phase_value).phaseDetails.all()
            }
            for dv in detail_values:
                self.assertIn(dv, present, msg=f"{dv} missing under {phase_value}")

    def test_phase_index_order_is_gap_free_and_matches_target(self):
        phases = list(ProjectPhase.objects.order_by("index"))
        self.assertEqual([p.value for p in phases], TARGET_PHASE_ORDER)
        for i, p in enumerate(phases):
            self.assertEqual(p.index, i)
            self.assertEqual(p.order, i)

    def test_moved_to_construction_reparented_to_construction_wait(self):
        detail = ProjectPhaseDetail.objects.get(value="movedToConstruction")
        self.assertEqual(detail.projectPhase.value, "constructionWait")
        # constructionPreparation keeps only contractPreparation.
        prep_details = {
            d.value
            for d in ProjectPhase.objects.get(value="constructionPreparation").phaseDetails.all()
        }
        self.assertEqual(prep_details, {"contractPreparation"})


class TaxonomyRestructureCallableTests(TestCase):
    def setUp(self):
        # Rebuild pre-restructure state via the migration's reverse, then drive
        # the forward callable against it.
        taxonomy_migration.reverse_restructure(django_apps, schema_editor=None)

        self.project_type, _ = ProjectType.objects.get_or_create(value="projectComplex")
        self.draft_initiation = ProjectPhase.objects.get(value="draftInitiation")
        self.draft_approval = ProjectPhase.objects.get(value="draftApproval")
        self.construction_plan = ProjectPhase.objects.get(value="constructionPlan")
        self.construction = ProjectPhase.objects.get(value="construction")
        self.construction_preparation = ProjectPhase.objects.get(value="constructionPreparation")
        self.construction_wait = ProjectPhase.objects.get(value="constructionWait")
        self.suspended = ProjectPhase.objects.get(value="suspended")
        self.first_phase_complete = ProjectPhaseDetail.objects.get(
            value=REMOVED_CONSTRUCTION_DETAIL, projectPhase=self.construction
        )
        self.moved_to_construction = ProjectPhaseDetail.objects.get(
            value="movedToConstruction", projectPhase=self.construction_preparation
        )

    def _make(self, name, phase, detail=None, suspended_from=None):
        return Project.objects.create(
            name=name, description=name, type=self.project_type,
            phase=phase, phaseDetail=detail, suspendedFromPhase=suspended_from,
        )

    def _restructure(self):
        taxonomy_migration.restructure_taxonomy(django_apps, schema_editor=None)

    def test_repoints_projects_to_planning_with_correct_detail(self):
        di = self._make("di", self.draft_initiation)
        da = self._make("da", self.draft_approval)
        cp = self._make("cp", self.construction_plan)

        self._restructure()

        planning = ProjectPhase.objects.get(value=PLANNING_PHASE_VALUE)
        for proj, expected_detail in [
            (di, "streetParkPlanDraft"),
            (da, "streetParkPlanApproval"),
            (cp, "constructionDesign"),
        ]:
            proj.refresh_from_db()
            self.assertEqual(proj.phase, planning)
            self.assertEqual(proj.phaseDetail.value, expected_detail)
            self.assertEqual(proj.phaseDetail.projectPhase, planning)

    def test_suspended_project_demoted_to_designplanning_detail(self):
        # IO-863: the standalone `suspended` phase is removed; the project moves to
        # designPlanning + the `suspended` detail. suspendedFromPhase is PRESERVED
        # (repointed off the deleted draftApproval phase to planning) so the change
        # stays reversible.
        susp = self._make("susp", self.suspended, suspended_from=self.draft_approval)
        self._restructure()
        susp.refresh_from_db()
        planning = ProjectPhase.objects.get(value=PLANNING_PHASE_VALUE)
        self.assertEqual(susp.phase, planning)
        self.assertEqual(susp.phaseDetail.value, SUSPENDED_DETAIL_VALUE)
        self.assertEqual(susp.phaseDetail.projectPhase, planning)
        self.assertEqual(susp.suspendedFromPhase.value, PLANNING_PHASE_VALUE)

    def test_reparents_moved_to_construction_and_its_projects(self):
        proj = self._make(
            "mtc", self.construction_preparation, detail=self.moved_to_construction
        )
        self._restructure()
        proj.refresh_from_db()
        self.assertEqual(proj.phase.value, "constructionWait")
        self.assertEqual(proj.phaseDetail.value, "movedToConstruction")
        self.assertEqual(proj.phaseDetail.projectPhase.value, "constructionWait")

    def test_first_phase_complete_moved_to_construction_wait(self):
        # IO-863 spec op 4: construction projects on the old "first phase complete"
        # detail move to constructionWait with the renamed firstPhaseCompleteOrIncomplete.
        on_fpc = self._make("fpc", self.construction, detail=self.first_phase_complete)
        pre_con = ProjectPhaseDetail.objects.get(value="preConstruction", projectPhase=self.construction)
        control = self._make("ctrl", self.construction, detail=pre_con)

        self._restructure()

        on_fpc.refresh_from_db()
        control.refresh_from_db()
        self.assertEqual(on_fpc.phase.value, "constructionWait")
        self.assertEqual(on_fpc.phaseDetail.value, "firstPhaseCompleteOrIncomplete")
        self.assertEqual(on_fpc.phaseDetail.projectPhase.value, "constructionWait")
        self.assertFalse(ProjectPhaseDetail.objects.filter(value=REMOVED_CONSTRUCTION_DETAIL).exists())
        self.assertEqual(control.phaseDetail, pre_con)  # untouched
        self.assertEqual(control.phase.value, "construction")  # untouched

    def test_warranty_projects_backfilled_with_warranty_detail(self):
        # IO-863 spec op 5: every warranty-period project gets the warranty detail.
        warranty_phase = ProjectPhase.objects.get(value="warrantyPeriod")
        proj = self._make("warr", warranty_phase)
        self._restructure()
        proj.refresh_from_db()
        self.assertEqual(proj.phase.value, "warrantyPeriod")
        self.assertEqual(proj.phaseDetail.value, "warranty")
        self.assertEqual(proj.phaseDetail.projectPhase.value, "warrantyPeriod")

    def test_deleted_phases_removed_and_no_dangling(self):
        self._make("di", self.draft_initiation)
        self._restructure()
        self.assertFalse(ProjectPhase.objects.filter(value__in=DELETED_PHASE_VALUES).exists())
        self.assertEqual(Project.objects.filter(phase__value__in=DELETED_PHASE_VALUES).count(), 0)

    def test_idempotent(self):
        di = self._make("di", self.draft_initiation)
        self._restructure()
        di.refresh_from_db()
        first = (di.phase_id, di.phaseDetail_id)
        self._restructure()
        di.refresh_from_db()
        self.assertEqual((di.phase_id, di.phaseDetail_id), first)
