"""Shared planning/construction schedule helpers.

A project's money may only land in years covered by its planning or
construction phase. Values at any other year are the data artefacts known
internally as "haamuluvut" (ghost numbers). Both the cleanup command
(``find_out_of_schedule_finances``) and the server-side prevention signal
(``reconcile_finances_on_schedule_change``) reason about the same year
range, so the logic lives here and is imported from both sites.
"""

from dataclasses import dataclass

from infraohjelmointi_api.models import Project


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

    def nearest_in_schedule_year(self, year: int) -> int | None:
        """Return the in-schedule year closest to ``year``.

        The candidates are the four phase boundaries; for any out-of-range
        year the nearest in-schedule year is always the closest edge of the
        nearest phase, so the boundaries are sufficient. Boundaries from an
        inverted/empty phase are dropped because they are not themselves
        in-schedule. On a tie the later year wins, mirroring the UI's
        "move forward" preference (``moveBudgetForwards`` /
        ``moveBudgetBackwards`` in ``financesUtils.ts``).

        Returns ``None`` when the project has no in-schedule year at all
        (e.g. every phase is empty), signalling the caller to leave the
        row untouched rather than destroy money on an unusable schedule.
        """
        candidates: list[int] = []
        if self.planning_start is not None and self.planning_end is not None:
            candidates += [self.planning_start, self.planning_end]
        if self.construction_start is not None and self.construction_end is not None:
            candidates += [self.construction_start, self.construction_end]

        in_range = [c for c in candidates if self.contains(c)]
        if not in_range:
            return None
        return min(in_range, key=lambda c: (abs(c - year), -c))


def resolve_schedule(project: Project) -> Schedule:
    return Schedule(
        planning_start=project.planningStartYear,
        planning_end=project.estPlanningEnd.year if project.estPlanningEnd else None,
        construction_start=(
            project.estConstructionStart.year if project.estConstructionStart else None
        ),
        construction_end=project.constructionEndYear,
    )
