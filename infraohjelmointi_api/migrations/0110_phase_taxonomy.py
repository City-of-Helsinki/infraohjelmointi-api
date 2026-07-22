"""IO-863: phase / phase-detail taxonomy change, in two data operations.

op 1 (backfill) — add the ``programming`` ProjectPhaseDetail under the
``programming`` phase and back-fill ``Project.phaseDetail`` for programming-phase
projects (see services/utils/phase_taxonomy.decide_programming_phase_detail_value).

op 2 (restructure) — collapse the three standalone planning phases
(draftInitiation/draftApproval/constructionPlan) into one ``planning``
("Suunnittelu") phase, moving their details under it; migrate every affected
project; add the new constructionWait/construction/warrantyPeriod details; move
construction "first phase complete" projects to ``constructionWait`` with the
renamed ``firstPhaseCompleteOrIncomplete`` detail (spec op 4); back-fill every
warranty-period project with the ``warranty`` detail (spec op 5); and renumber
every phase's index/order.

Ordering inside op 2 is load-bearing: Project.phase / phaseDetail /
suspendedFromPhase are all DO_NOTHING + DEFERRABLE FKs, so every referencing
project is repointed BEFORE any phase/detail row is deleted (a delete-first would
dangle the FK and fail at COMMIT). Moved details are re-parented in place (never
recreated) so existing project->detail FKs stay valid. All project writes use
bulk_update/.update() to bypass the on_project_phase_change signal (no spurious
K1 category writes or SSE events for a one-shot data migration).
"""

import logging

from django.db import migrations

from infraohjelmointi_api.services.utils.phase_taxonomy import (
    DELETED_PHASE_TO_DETAIL,
    DELETED_PHASE_VALUES,
    FIRST_PHASE_COMPLETE_TARGET_DETAIL,
    FIRST_PHASE_COMPLETE_TARGET_PHASE,
    MOVED_DETAILS,
    NEW_DETAILS,
    PLANNING_PHASE_VALUE,
    PROGRAMMING_DETAIL_VALUE,
    REMOVED_CONSTRUCTION_DETAIL,
    REPARENTED_DETAILS,
    SUSPENDED_DETAIL_VALUE,
    SUSPENDED_PHASE_VALUE,
    TARGET_PHASE_ORDER,
    WAITING_PLANNING_START_DETAIL_VALUE,
    WAITING_PROJECT_MANAGER_DETAIL_VALUE,
    WARRANTY_BACKFILL_DETAIL_VALUE,
    WARRANTY_PHASE_VALUE,
    decide_programming_phase_detail_value,
)

logger = logging.getLogger("infraohjelmointi_api")

BULK_UPDATE_BATCH_SIZE = 500


def _invalidate_lookup_caches():
    """Best-effort: the phase/detail list endpoints cache for 12h and migrations
    don't fire the cache-invalidation signal. Never let a cache miss fail the
    migration (the backend may be absent in CI / during deploy)."""
    try:
        from infraohjelmointi_api.services.CacheService import CacheService

        for model_name in ("ProjectPhase", "ProjectPhaseDetail"):
            CacheService.invalidate_lookup(model_name)
    except Exception as exc:  # noqa: BLE001 - best effort only
        logger.warning("IO-863: lookup cache invalidation skipped (%s)", exc)


# === op 1: programming backfill ===

def backfill_programming(apps, schema_editor):
    ProjectPhase = apps.get_model("infraohjelmointi_api", "ProjectPhase")
    ProjectPhaseDetail = apps.get_model("infraohjelmointi_api", "ProjectPhaseDetail")
    Project = apps.get_model("infraohjelmointi_api", "Project")

    programming_phase = ProjectPhase.objects.filter(value="programming").first()
    if not programming_phase:
        return

    # Ensure every detail the backfill can assign exists under the programming
    # phase. `waiting*` were created in 0097, but get_or_create keeps this robust
    # (a missing target would otherwise silently skip 2026 projects).
    for detail_value in (
        PROGRAMMING_DETAIL_VALUE,
        WAITING_PLANNING_START_DETAIL_VALUE,
        WAITING_PROJECT_MANAGER_DETAIL_VALUE,
    ):
        ProjectPhaseDetail.objects.get_or_create(
            value=detail_value,
            projectPhase=programming_phase,
        )

    detail_by_value = {
        d.value: d
        for d in ProjectPhaseDetail.objects.filter(projectPhase=programming_phase)
    }

    projects_to_update = []
    qs = Project.objects.filter(phase=programming_phase).only(
        "id", "planningStartYear", "personPlanning_id", "phaseDetail_id"
    )
    for project in qs.iterator(chunk_size=1000):
        target_value = decide_programming_phase_detail_value(
            planning_start_year=project.planningStartYear,
            has_planning_person=project.personPlanning_id is not None,
        )
        if target_value is None:
            continue
        target_detail = detail_by_value.get(target_value)
        if target_detail is None:
            continue
        if project.phaseDetail_id == target_detail.id:
            continue
        project.phaseDetail = target_detail
        projects_to_update.append(project)

    if projects_to_update:
        Project.objects.bulk_update(
            projects_to_update, ["phaseDetail"], batch_size=BULK_UPDATE_BATCH_SIZE
        )


def reverse_backfill(apps, schema_editor):
    """Drop the ``programming`` detail; deliberately do NOT undo the backfill
    (a data fix, not a schema change)."""
    ProjectPhaseDetail = apps.get_model("infraohjelmointi_api", "ProjectPhaseDetail")
    Project = apps.get_model("infraohjelmointi_api", "Project")

    Project.objects.filter(phaseDetail__value=PROGRAMMING_DETAIL_VALUE).update(
        phaseDetail=None
    )
    ProjectPhaseDetail.objects.filter(value=PROGRAMMING_DETAIL_VALUE).delete()


# === op 2: taxonomy restructure ===

def restructure_taxonomy(apps, schema_editor):
    ProjectPhase = apps.get_model("infraohjelmointi_api", "ProjectPhase")
    ProjectPhaseDetail = apps.get_model("infraohjelmointi_api", "ProjectPhaseDetail")
    Project = apps.get_model("infraohjelmointi_api", "Project")

    # Step 0 — pre-flight audit log.
    for dpv in DELETED_PHASE_VALUES:
        logger.info(
            "IO-863: %s project(s) in phase '%s'",
            Project.objects.filter(phase__value=dpv).count(),
            dpv,
        )
    logger.info(
        "IO-863: %s project(s) on detail '%s'",
        Project.objects.filter(
            phaseDetail__value=REMOVED_CONSTRUCTION_DETAIL,
            phaseDetail__projectPhase__value="construction",
        ).count(),
        REMOVED_CONSTRUCTION_DETAIL,
    )
    logger.info(
        "IO-863: %s project(s) with suspendedFromPhase in a deleted phase",
        Project.objects.filter(suspendedFromPhase__value__in=DELETED_PHASE_VALUES).count(),
    )

    # Step 1 — create the new Suunnittelu phase (index/order set in step 8).
    planning, _ = ProjectPhase.objects.get_or_create(value=PLANNING_PHASE_VALUE)

    # Step 2 — re-parent the moved planning details onto `planning` IN PLACE
    # (same row id, so projects already pointing at them stay valid).
    for detail_value in MOVED_DETAILS:
        ProjectPhaseDetail.objects.filter(value=detail_value).update(projectPhase=planning)

    # Step 3 — create the new details under their phases (idempotent).
    for phase_value, detail_values in NEW_DETAILS.items():
        phase = ProjectPhase.objects.filter(value=phase_value).first()
        if not phase:
            continue
        for dv in detail_values:
            ProjectPhaseDetail.objects.get_or_create(value=dv, projectPhase=phase)

    # Step 4 — repoint every project off a deleted phase onto `planning` with the
    # corresponding detail, BEFORE the phases are deleted.
    detail_by_value = {
        d.value: d for d in ProjectPhaseDetail.objects.filter(projectPhase=planning)
    }
    projects_to_update = []
    for dpv, target_detail_value in DELETED_PHASE_TO_DETAIL.items():
        dphase = ProjectPhase.objects.filter(value=dpv).first()
        if not dphase:
            continue
        target_detail = detail_by_value.get(target_detail_value)
        if target_detail is None:
            # Defensive: the moved detail isn't under planning — skip rather than
            # repoint to a wrong/empty detail.
            continue
        for project in Project.objects.filter(phase=dphase).only(
            "id", "phase_id", "phaseDetail_id"
        ).iterator(chunk_size=1000):
            project.phase = planning
            project.phaseDetail = target_detail
            projects_to_update.append(project)
    if projects_to_update:
        Project.objects.bulk_update(
            projects_to_update, ["phase", "phaseDetail"], batch_size=BULK_UPDATE_BATCH_SIZE
        )

    # Step 5 — repoint suspendedFromPhase references off the deleted phases.
    Project.objects.filter(suspendedFromPhase__value__in=DELETED_PHASE_VALUES).update(
        suspendedFromPhase=planning
    )

    # Step 5b — move reparented details (and their projects) to their new phase.
    # IO-863: movedToConstruction moves constructionPreparation -> constructionWait.
    # Projects move with it so phase and phaseDetail stay consistent (the validator
    # requires phaseDetail.projectPhase == project.phase).
    for detail_value, (old_phase_value, new_phase_value) in REPARENTED_DETAILS.items():
        new_phase = ProjectPhase.objects.filter(value=new_phase_value).first()
        detail = ProjectPhaseDetail.objects.filter(
            value=detail_value, projectPhase__value=old_phase_value
        ).first()
        if not (new_phase and detail):
            continue  # already moved (idempotent re-run) or missing
        moved = Project.objects.filter(phaseDetail=detail).count()
        if moved:
            logger.info(
                "IO-863: moving %s project(s) with detail '%s' from '%s' to '%s'",
                moved, detail_value, old_phase_value, new_phase_value,
            )
        Project.objects.filter(phaseDetail=detail).update(phase=new_phase)
        detail.projectPhase = new_phase
        detail.save(update_fields=["projectPhase"])

    # Step 6 — IO-863 spec op 4 ("Rakentamishankkeet"): move construction projects
    # that were "first phase complete" to the constructionWait phase with the renamed
    # firstPhaseCompleteOrIncomplete detail, then drop the obsolete firstPhaseComplete
    # row. Projects are repointed to the new (phase, detail) BEFORE the old row is
    # deleted, so no FK dangles and phase/phaseDetail stay consistent.
    fpc = ProjectPhaseDetail.objects.filter(
        value=REMOVED_CONSTRUCTION_DETAIL, projectPhase__value="construction"
    ).first()
    if fpc:
        target_phase = ProjectPhase.objects.filter(
            value=FIRST_PHASE_COMPLETE_TARGET_PHASE
        ).first()
        target_detail = ProjectPhaseDetail.objects.filter(
            value=FIRST_PHASE_COMPLETE_TARGET_DETAIL, projectPhase=target_phase
        ).first()
        affected = Project.objects.filter(phaseDetail=fpc).count()
        if target_phase and target_detail:
            if affected:
                logger.info(
                    "IO-863: moving %s project(s) from construction/'%s' to '%s'/'%s'",
                    affected,
                    REMOVED_CONSTRUCTION_DETAIL,
                    FIRST_PHASE_COMPLETE_TARGET_PHASE,
                    FIRST_PHASE_COMPLETE_TARGET_DETAIL,
                )
            Project.objects.filter(phaseDetail=fpc).update(
                phase=target_phase, phaseDetail=target_detail
            )
        else:
            # Defensive: the move target is missing — NULL the detail so the row can
            # still be removed without dangling FKs (don't lose the phase).
            logger.warning(
                "IO-863: move target '%s'/'%s' missing; NULLing phaseDetail on %s "
                "construction project(s) instead",
                FIRST_PHASE_COMPLETE_TARGET_PHASE,
                FIRST_PHASE_COMPLETE_TARGET_DETAIL,
                affected,
            )
            Project.objects.filter(phaseDetail=fpc).update(phaseDetail=None)
        fpc.delete()

    # Step 6b — IO-863 spec op 5 ("Takuuajan hankkeet"): every warranty-period
    # project gets the warranty detail. Idempotent via .exclude().
    warranty_phase = ProjectPhase.objects.filter(value=WARRANTY_PHASE_VALUE).first()
    warranty_detail = (
        ProjectPhaseDetail.objects.filter(
            value=WARRANTY_BACKFILL_DETAIL_VALUE, projectPhase=warranty_phase
        ).first()
        if warranty_phase
        else None
    )
    if warranty_phase and warranty_detail:
        to_backfill = Project.objects.filter(phase=warranty_phase).exclude(
            phaseDetail=warranty_detail
        )
        affected = to_backfill.count()
        if affected:
            logger.info(
                "IO-863: assigning '%s' detail to %s warranty-period project(s)",
                WARRANTY_BACKFILL_DETAIL_VALUE,
                affected,
            )
            to_backfill.update(phaseDetail=warranty_detail)

    # Step 6c — IO-863: demote the standalone `suspended` phase to the `suspended`
    # detail under designPlanning (spec table: the top-level "Keskeytetty" phase is
    # removed; "Keskeytetty toistaiseksi" becomes a Suunnittelu detail). Move every
    # suspended-phase project to designPlanning + the suspended detail, then delete
    # the phase. suspendedFromPhase is PRESERVED (not nulled) so the change stays
    # reversible — a follow-up migration could restore cross-phase suspension from it.
    # Only a pathological suspended-from-suspended self-reference is cleared so the
    # row can be deleted without a dangling FK.
    suspended_phase = ProjectPhase.objects.filter(value=SUSPENDED_PHASE_VALUE).first()
    if suspended_phase:
        suspended_detail = ProjectPhaseDetail.objects.filter(
            value=SUSPENDED_DETAIL_VALUE, projectPhase=planning
        ).first()
        if suspended_detail:
            moved = Project.objects.filter(phase=suspended_phase).count()
            if moved:
                logger.info(
                    "IO-863: demoting %s suspended-phase project(s) to designPlanning "
                    "+ '%s' detail (suspendedFromPhase preserved)",
                    moved,
                    SUSPENDED_DETAIL_VALUE,
                )
            Project.objects.filter(phase=suspended_phase).update(
                phase=planning, phaseDetail=suspended_detail
            )
        Project.objects.filter(suspendedFromPhase=suspended_phase).update(
            suspendedFromPhase=None
        )
        remaining = Project.objects.filter(phase=suspended_phase).count()
        if remaining:
            raise RuntimeError(
                f"IO-863: {remaining} project(s) still on the suspended phase after "
                "demotion; aborting to avoid a dangling FK."
            )
        suspended_phase.delete()

    # Step 7 — delete the merged-away phases (now unreferenced). Guard first.
    remaining = Project.objects.filter(phase__value__in=DELETED_PHASE_VALUES).count()
    if remaining:
        raise RuntimeError(
            f"IO-863: {remaining} project(s) still reference a deleted planning "
            "phase after repointing; aborting to avoid dangling FKs."
        )
    ProjectPhase.objects.filter(value__in=DELETED_PHASE_VALUES).delete()

    # Step 8 — deterministic absolute index/order over the surviving phases.
    for i, value in enumerate(TARGET_PHASE_ORDER):
        ProjectPhase.objects.filter(value=value).update(index=i, order=i)

    # Step 9 — best-effort lookup cache invalidation.
    _invalidate_lookup_caches()


def reverse_restructure(apps, schema_editor):
    """Restore the lookup rows so the migration graph can move backward. We do
    NOT reconstruct per-project phase history (projects stay on `planning`); the
    `planning` phase is kept because projects reference it."""
    ProjectPhase = apps.get_model("infraohjelmointi_api", "ProjectPhase")
    ProjectPhaseDetail = apps.get_model("infraohjelmointi_api", "ProjectPhaseDetail")
    Project = apps.get_model("infraohjelmointi_api", "Project")

    # Re-create the three deleted phases at the tail (0097 reverse pattern).
    from django.db.models import Max

    max_order = ProjectPhase.objects.aggregate(Max("order"))["order__max"] or -1
    for offset, value in enumerate(DELETED_PHASE_VALUES, start=1):
        ProjectPhase.objects.get_or_create(
            value=value,
            defaults={"order": max_order + offset, "index": max_order + offset},
        )

    # IO-863 reverse: re-create the `suspended` phase and move its projects back to
    # it (their preserved `suspendedFromPhase` stays intact). Done before the
    # new-detail cleanup below, which would otherwise only NULL their phaseDetail in
    # place and leave them on designPlanning.
    suspended_offset = len(DELETED_PHASE_VALUES) + 1
    suspended_phase, _ = ProjectPhase.objects.get_or_create(
        value=SUSPENDED_PHASE_VALUE,
        defaults={
            "order": max_order + suspended_offset,
            "index": max_order + suspended_offset,
        },
    )
    planning = ProjectPhase.objects.filter(value=PLANNING_PHASE_VALUE).first()
    if planning:
        suspended_detail = ProjectPhaseDetail.objects.filter(
            value=SUSPENDED_DETAIL_VALUE, projectPhase=planning
        ).first()
        if suspended_detail:
            Project.objects.filter(phaseDetail=suspended_detail).update(
                phase=suspended_phase, phaseDetail=None
            )

    # Move the planning details back under their original phases.
    for detail_value, old_phase_value in MOVED_DETAILS.items():
        old_phase = ProjectPhase.objects.filter(value=old_phase_value).first()
        if old_phase:
            ProjectPhaseDetail.objects.filter(value=detail_value).update(
                projectPhase=old_phase
            )

    # Move reparented details back to their original phase (projects are NOT moved
    # back — same "don't reconstruct per-project history" rule).
    for detail_value, (old_phase_value, _new) in REPARENTED_DETAILS.items():
        old_phase = ProjectPhase.objects.filter(value=old_phase_value).first()
        if old_phase:
            ProjectPhaseDetail.objects.filter(value=detail_value).update(
                projectPhase=old_phase
            )

    # Delete the new details (NULL Project FKs first).
    new_detail_values = [dv for values in NEW_DETAILS.values() for dv in values]
    Project.objects.filter(phaseDetail__value__in=new_detail_values).update(
        phaseDetail=None
    )
    ProjectPhaseDetail.objects.filter(value__in=new_detail_values).delete()

    # Re-create firstPhaseComplete under construction (do not reattach projects).
    construction = ProjectPhase.objects.filter(value="construction").first()
    if construction:
        ProjectPhaseDetail.objects.get_or_create(
            value=REMOVED_CONSTRUCTION_DETAIL, projectPhase=construction
        )

    _invalidate_lookup_caches()


class Migration(migrations.Migration):
    dependencies = [
        ("infraohjelmointi_api", "0109_merge_20260617_1214"),
    ]

    operations = [
        migrations.RunPython(backfill_programming, reverse_backfill),
        migrations.RunPython(restructure_taxonomy, reverse_restructure),
    ]
