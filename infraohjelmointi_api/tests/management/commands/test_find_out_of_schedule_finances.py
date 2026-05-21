"""Tests for the IO-841 ``find_out_of_schedule_finances`` management command.

Each test sets up a single ``Project`` (or two) with a controlled
schedule and a handful of ``ProjectFinancial`` rows, then runs the
command in either dry-run or ``--apply`` mode and asserts on stdout
(the CSV report) and on the database.
"""

from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from infraohjelmointi_api.models import Project, ProjectFinancial


def _create_project(
    *,
    name: str = "Test project",
    planning_start_year: int | None = 2024,
    est_planning_end: date | None = date(2025, 6, 30),
    est_construction_start: date | None = date(2026, 1, 1),
    construction_end_year: int | None = 2028,
) -> Project:
    return Project.objects.create(
        name=name,
        description="-",
        planningStartYear=planning_start_year,
        estPlanningEnd=est_planning_end,
        estConstructionStart=est_construction_start,
        constructionEndYear=construction_end_year,
    )


def _create_finance(
    project: Project,
    *,
    year: int,
    value: str | Decimal,
    for_frame_view: bool = False,
) -> ProjectFinancial:
    return ProjectFinancial.objects.create(
        project=project,
        year=year,
        value=Decimal(value),
        forFrameView=for_frame_view,
    )


def _run(*args: str) -> str:
    out = StringIO()
    err = StringIO()
    call_command("find_out_of_schedule_finances", *args, stdout=out, stderr=err)
    return out.getvalue()


class FindOutOfScheduleFinancesTestCase(TestCase):
    """The schedule for these tests is planning 2024-2025 + construction 2026-2028.

    That means in-schedule years are {2024, 2025, 2026, 2027, 2028} and
    everything else (e.g. 2023, 2029, 2030, …) is a haamuluku candidate.
    """

    def test_in_schedule_years_are_left_alone(self) -> None:
        project = _create_project()
        for year in (2024, 2025, 2026, 2027, 2028):
            _create_finance(project, year=year, value="100.00")

        output = _run()

        self.assertNotIn("would_zero", output)
        self.assertNotIn("zeroed", output)
        for fin in ProjectFinancial.objects.filter(project=project):
            self.assertEqual(fin.value, Decimal("100.00"))

    def test_dry_run_reports_haamuluku_without_writing(self) -> None:
        project = _create_project()
        haamu = _create_finance(project, year=2030, value="2000.00")
        keep = _create_finance(project, year=2025, value="500.00")

        output = _run()

        self.assertIn("would_zero", output)
        self.assertIn(str(project.id), output)
        self.assertIn("2030", output)
        haamu.refresh_from_db()
        keep.refresh_from_db()
        self.assertEqual(haamu.value, Decimal("2000.00"))
        self.assertEqual(keep.value, Decimal("500.00"))

    def test_apply_zeroes_only_haamuluvut(self) -> None:
        project = _create_project()
        haamu = _create_finance(project, year=2030, value="2000.00")
        keep = _create_finance(project, year=2025, value="500.00")

        output = _run("--apply")

        self.assertIn("zeroed", output)
        haamu.refresh_from_db()
        keep.refresh_from_db()
        self.assertEqual(haamu.value, Decimal("0"))
        self.assertEqual(keep.value, Decimal("500.00"))

    def test_negative_values_are_treated_as_haamulukuja(self) -> None:
        project = _create_project()
        haamu = _create_finance(project, year=2030, value="-50.00")

        _run("--apply")

        haamu.refresh_from_db()
        self.assertEqual(haamu.value, Decimal("0"))

    def test_zero_valued_rows_are_not_touched(self) -> None:
        project = _create_project()
        zero = _create_finance(project, year=2030, value="0.00")

        output = _run("--apply")

        self.assertNotIn("would_zero", output)
        self.assertNotIn("zeroed", output)
        zero.refresh_from_db()
        self.assertEqual(zero.value, Decimal("0.00"))

    def test_overlapping_planning_and_construction_keeps_overlap_year(self) -> None:
        project = _create_project(
            est_planning_end=date(2026, 6, 30),
            est_construction_start=date(2026, 1, 1),
        )
        overlap = _create_finance(project, year=2026, value="999.00")

        _run("--apply")

        overlap.refresh_from_db()
        self.assertEqual(overlap.value, Decimal("999.00"))

    def test_inverted_planning_dates_treat_planning_phase_as_empty(self) -> None:
        project = _create_project(
            planning_start_year=2025,
            est_planning_end=date(2024, 6, 30),
        )
        in_construction = _create_finance(project, year=2027, value="100.00")
        haamu_in_inverted_planning = _create_finance(
            project, year=2024, value="50.00"
        )

        _run("--apply")

        in_construction.refresh_from_db()
        haamu_in_inverted_planning.refresh_from_db()
        self.assertEqual(in_construction.value, Decimal("100.00"))
        self.assertEqual(haamu_in_inverted_planning.value, Decimal("0"))

    def test_project_with_null_schedule_field_is_skipped(self) -> None:
        project = _create_project(est_planning_end=None)
        suspect = _create_finance(project, year=2030, value="2000.00")

        output = _run("--apply")

        self.assertIn("skipped_no_schedule", output)
        suspect.refresh_from_db()
        self.assertEqual(suspect.value, Decimal("2000.00"))

    def test_frame_view_row_is_not_touched_by_default(self) -> None:
        project = _create_project()
        frame_haamu = _create_finance(
            project, year=2030, value="123.00", for_frame_view=True
        )
        regular_haamu = _create_finance(project, year=2030, value="456.00")

        _run("--apply")

        frame_haamu.refresh_from_db()
        regular_haamu.refresh_from_db()
        self.assertEqual(frame_haamu.value, Decimal("123.00"))
        self.assertEqual(regular_haamu.value, Decimal("0"))

    def test_include_frame_view_flag_zeroes_both(self) -> None:
        project = _create_project()
        frame_haamu = _create_finance(
            project, year=2030, value="123.00", for_frame_view=True
        )
        regular_haamu = _create_finance(project, year=2030, value="456.00")

        _run("--apply", "--include-frame-view")

        frame_haamu.refresh_from_db()
        regular_haamu.refresh_from_db()
        self.assertEqual(frame_haamu.value, Decimal("0"))
        self.assertEqual(regular_haamu.value, Decimal("0"))

    def test_csv_header_present_unless_quiet(self) -> None:
        _create_project()

        with_header = _run()
        without_header = _run("--quiet")

        self.assertIn("projectId", with_header.splitlines()[0])
        self.assertNotIn("projectId", without_header)

    def test_limit_caps_processed_projects(self) -> None:
        for i in range(3):
            project = _create_project(name=f"P{i}")
            _create_finance(project, year=2030, value="10.00")

        output = _run("--limit", "1")

        haamuluku_lines = [
            line for line in output.splitlines() if "would_zero" in line
        ]
        self.assertEqual(len(haamuluku_lines), 1)

    def test_non_positive_limit_is_rejected(self) -> None:
        for value in ("0", "-1"):
            with self.subTest(value=value):
                with self.assertRaises(CommandError):
                    _run("--limit", value)

    def test_summary_log_line_emitted_to_stderr(self) -> None:
        project = _create_project()
        _create_finance(project, year=2030, value="2000.00")
        out = StringIO()
        err = StringIO()
        call_command(
            "find_out_of_schedule_finances", stdout=out, stderr=err
        )

        self.assertIn("Would zero", err.getvalue())
        self.assertIn("haamuluk", err.getvalue())

    def test_apply_updates_updated_date(self) -> None:
        project = _create_project()
        haamu = _create_finance(project, year=2030, value="2000.00")
        original_updated = haamu.updatedDate

        _run("--apply")

        haamu.refresh_from_db()
        self.assertGreater(haamu.updatedDate, original_updated)
