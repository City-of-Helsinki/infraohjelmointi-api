"""Find (and optionally zero) ProjectFinancial rows whose year falls
outside the project's planning and construction schedule — the data
artefacts known internally as "haamuluvut" (ghost numbers). See
``tickets/IO-841.md`` for full background and design notes.

Default mode is dry-run: the command prints a CSV report and never writes.
With ``--apply`` it zeroes the offending rows in place via ``save()`` so
that the cache-invalidation and event-stream signals defined in
``signals.py`` fire correctly.
"""

import argparse
import csv
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from infraohjelmointi_api.models import Project, ProjectFinancial


logger = logging.getLogger("infraohjelmointi_api")


CSV_HEADER = [
    "projectId",
    "projectName",
    "hkrId",
    "sapProject",
    "programmed",
    "phase",
    "planningStartYear",
    "estPlanningEnd",
    "estConstructionStart",
    "constructionEndYear",
    "forFrameView",
    "year",
    "value",
    "action",
]


@dataclass(frozen=True)
class Schedule:
    """Resolved planning + construction year range for a project.

    A range with ``start > end`` is treated as empty so that data with
    inverted dates (e.g. ``estPlanningEnd < planningStartYear``) does not
    silently mark every year as in-schedule.
    """

    planning_start: int | None
    planning_end: int | None
    construction_start: int | None
    construction_end: int | None

    @property
    def is_complete(self) -> bool:
        return all(
            v is not None
            for v in (
                self.planning_start,
                self.planning_end,
                self.construction_start,
                self.construction_end,
            )
        )

    def contains(self, year: int) -> bool:
        in_planning = (
            self.planning_start is not None
            and self.planning_end is not None
            and self.planning_start <= year <= self.planning_end
        )
        in_construction = (
            self.construction_start is not None
            and self.construction_end is not None
            and self.construction_start <= year <= self.construction_end
        )
        return in_planning or in_construction


def _resolve_schedule(project: Project) -> Schedule:
    return Schedule(
        planning_start=project.planningStartYear,
        planning_end=project.estPlanningEnd.year if project.estPlanningEnd else None,
        construction_start=(
            project.estConstructionStart.year if project.estConstructionStart else None
        ),
        construction_end=project.constructionEndYear,
    )


def _positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue < 1:
        raise argparse.ArgumentTypeError(
            f"--limit must be a positive integer (got {ivalue})"
        )
    return ivalue


class Command(BaseCommand):
    help = (
        "Find ProjectFinancial rows whose year is outside the project's "
        "planning/construction schedule (haamuluvut, IO-841). "
        "Dry-run by default; pass --apply to zero the rows."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help=(
                "Zero the offending rows in the database. Without this "
                "flag, the command only reports what it would do."
            ),
        )
        parser.add_argument(
            "--include-frame-view",
            action="store_true",
            default=False,
            help=(
                "Also process ProjectFinancial rows with forFrameView=True. "
                "Default is forFrameView=False only, matching the scope of "
                "IO-826's prevention fix."
            ),
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            default=False,
            help="Suppress the CSV header and the summary log lines.",
        )
        parser.add_argument(
            "--limit",
            type=_positive_int,
            default=None,
            help="Process at most N projects (development aid). Must be >= 1.",
        )

    def handle(self, *args, **options):
        apply_changes: bool = options["apply"]
        include_frame_view: bool = options["include_frame_view"]
        quiet: bool = options["quiet"]
        limit: int | None = options["limit"]

        for_frame_view_values: tuple[bool, ...] = (
            (False, True) if include_frame_view else (False,)
        )

        writer = csv.writer(self.stdout)
        if not quiet:
            writer.writerow(CSV_HEADER)

        projects_qs = Project.objects.all().order_by("id")
        if limit is not None:
            projects_qs = projects_qs[:limit]

        report = _Report()

        for project in projects_qs.iterator():
            schedule = _resolve_schedule(project)

            if not schedule.is_complete:
                self._emit_skip_row(writer, project, schedule)
                report.skipped_projects += 1
                continue

            self._process_project(
                project=project,
                schedule=schedule,
                for_frame_view_values=for_frame_view_values,
                apply_changes=apply_changes,
                writer=writer,
                report=report,
            )

        if not quiet:
            self._log_summary(report=report, apply_changes=apply_changes)

    def _process_project(
        self,
        *,
        project: Project,
        schedule: Schedule,
        for_frame_view_values: tuple[bool, ...],
        apply_changes: bool,
        writer,
        report: "_Report",
    ) -> None:
        candidates = (
            ProjectFinancial.objects.filter(
                project=project,
                forFrameView__in=for_frame_view_values,
            )
            .filter(Q(value__gt=0) | Q(value__lt=0))
            .order_by("year", "forFrameView")
        )

        haamuluvut = [c for c in candidates if not schedule.contains(c.year)]
        if not haamuluvut:
            return

        # Snapshot the original values BEFORE we (potentially) zero them so the
        # CSV row and the summary report show what was destroyed, not zero.
        original_values = [row.value or Decimal("0") for row in haamuluvut]

        if apply_changes:
            self._zero_in_transaction(project=project, rows=haamuluvut)

        for row, original_value in zip(haamuluvut, original_values):
            self._emit_row(
                writer=writer,
                project=project,
                schedule=schedule,
                fin=row,
                value=original_value,
                action="zeroed" if apply_changes else "would_zero",
            )
            report.haamulukuja += 1
            report.total_value += original_value
            report.affected_project_ids.add(project.id)

    @staticmethod
    def _zero_in_transaction(
        *, project: Project, rows: Iterable[ProjectFinancial]
    ) -> None:
        with transaction.atomic():
            for row in rows:
                row.value = Decimal("0")
                row.save(update_fields=["value", "updatedDate"])

    @staticmethod
    def _emit_row(
        *,
        writer,
        project: Project,
        schedule: Schedule,
        fin: ProjectFinancial,
        value: Decimal,
        action: str,
    ) -> None:
        writer.writerow(
            [
                project.id,
                project.name,
                project.hkrId or "",
                project.sapProject or "",
                project.programmed,
                project.phase.value if project.phase else "",
                schedule.planning_start if schedule.planning_start is not None else "",
                project.estPlanningEnd.isoformat() if project.estPlanningEnd else "",
                (
                    project.estConstructionStart.isoformat()
                    if project.estConstructionStart
                    else ""
                ),
                (
                    schedule.construction_end
                    if schedule.construction_end is not None
                    else ""
                ),
                fin.forFrameView,
                fin.year,
                value,
                action,
            ]
        )

    @staticmethod
    def _emit_skip_row(writer, project: Project, schedule: Schedule) -> None:
        writer.writerow(
            [
                project.id,
                project.name,
                project.hkrId or "",
                project.sapProject or "",
                project.programmed,
                project.phase.value if project.phase else "",
                schedule.planning_start if schedule.planning_start is not None else "",
                project.estPlanningEnd.isoformat() if project.estPlanningEnd else "",
                (
                    project.estConstructionStart.isoformat()
                    if project.estConstructionStart
                    else ""
                ),
                (
                    schedule.construction_end
                    if schedule.construction_end is not None
                    else ""
                ),
                "",
                "",
                "",
                "skipped_no_schedule",
            ]
        )

    def _log_summary(self, *, report: "_Report", apply_changes: bool) -> None:
        verb = "Zeroed" if apply_changes else "Would zero"
        message = (
            f"{verb} {report.haamulukuja} haamulukua "
            f"totaling {report.total_value} € across "
            f"{len(report.affected_project_ids)} project(s); "
            f"skipped {report.skipped_projects} project(s) with incomplete schedule."
        )
        logger.info(message)
        # stderr so the CSV on stdout stays machine-readable
        self.stderr.write(message)


@dataclass
class _Report:
    haamulukuja: int = 0
    total_value: Decimal = Decimal("0")
    skipped_projects: int = 0
    affected_project_ids: set = field(default_factory=set)
