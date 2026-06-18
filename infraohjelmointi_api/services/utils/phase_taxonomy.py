"""IO-863: single source of truth for the project phase / phase-detail taxonomy
change, shared by the ``0109_phase_taxonomy`` migration and its unit tests so
neither has to pull in Django models.

Two concerns live here:

1. The programming-phase backfill decision (``decide_programming_phase_detail_value``),
   carried over verbatim from the earlier ``programming_phase_backfill`` helper.
2. The taxonomy restructure constants: which phases merge into the new
   ``planning`` ("Suunnittelu") phase, which details move, which are new, and the
   final phase ordering.

Labels are intentionally NOT here: ``ProjectPhase`` / ``ProjectPhaseDetail`` only
store ``value`` (+ ``index``/``order``). The Finnish labels live in the frontend
(``i18n/fi.json``) and the ProjectWise maps (``FieldMappingDictionaries``). The
label each value maps to is noted in comments for the PW follow-up.
"""

from typing import Optional


# === Programming-phase backfill (op 1) ===

PROGRAMMING_DETAIL_VALUE = "programming"
WAITING_PLANNING_START_DETAIL_VALUE = "waitingPlanningStart"
WAITING_PROJECT_MANAGER_DETAIL_VALUE = "waitingProjectManager"


def decide_programming_phase_detail_value(
    planning_start_year: Optional[int],
    has_planning_person: bool,
) -> Optional[str]:
    """Return the ``ProjectPhaseDetail.value`` that the IO-863 backfill should
    assign to a programming-phase project, or ``None`` if the project should
    keep whatever ``phaseDetail`` it already has.

    Rules from the customer spec on IO-863 (Fanny's clarification comment):

    * planningStartYear >= 2027, or empty/unknown ("tai on tyhjä") -> "programming"
    * planningStartYear == 2026 and project manager is named -> "waitingPlanningStart"
    * planningStartYear == 2026 and no project manager -> "waitingProjectManager"
    * < 2026 -> leave existing detail untouched

    Note: the spec phrases this against the "suunnittelu alkaa" date field, but the
    backfill keys on ``planningStartYear`` because that is the canonical planning
    start year across the codebase (see ``utils.schedule.resolve_schedule``).
    """
    if planning_start_year is None or planning_start_year >= 2027:
        return PROGRAMMING_DETAIL_VALUE
    if planning_start_year == 2026:
        if has_planning_person:
            return WAITING_PLANNING_START_DETAIL_VALUE
        return WAITING_PROJECT_MANAGER_DETAIL_VALUE
    return None


# === Taxonomy restructure (op 2) ===

PLANNING_PHASE_VALUE = "designPlanning"  # label "Suunnittelu"
# (value is "designPlanning", not "planning", to avoid colliding with the existing
#  i18n key option.planning = "Suunnitteluvaiheen" used by the constructionPhases lookup)

# The three standalone planning phases that collapse into ``planning``. Their
# single detail each (see MOVED_DETAILS) is re-parented under ``planning``.
DELETED_PHASE_VALUES = ["draftInitiation", "draftApproval", "constructionPlan"]

# detail value -> the (now deleted) phase it currently lives under. Every one of
# these details is re-parented to the ``planning`` phase.
MOVED_DETAILS = {
    "streetParkPlanDraft": "draftInitiation",       # Katu- ja puistosuunnittelun aloitus/suunnitelmaluonnos
    "streetParkPlanApproval": "draftApproval",      # Katu-/puistosuunnitelmaehdotus ja hyväksyminen
    "constructionDesign": "constructionPlan",       # Rakennussuunnittelu
}

# When a project sits on a deleted phase we repoint it to ``planning`` and assign
# the detail that corresponds to its old phase. Derived (inverted) from
# MOVED_DETAILS so the mapping can never drift out of sync / get swapped.
DELETED_PHASE_TO_DETAIL = {phase: detail for detail, phase in MOVED_DETAILS.items()}

# New details to create: phase value -> [detail values]. Labels:
#   firstPhaseCompleteOrIncomplete -> "Ensimmäinen vaihe valmis/keskeneräinen"
#   otherReason                    -> "Muu syy"
#   constructionStage              -> "Rakentaminen"
#   warranty                       -> "Takuuaika"
#   warrantyIncomplete             -> "Takuuaika/keskeneräinen"
NEW_DETAILS = {
    "constructionWait": ["firstPhaseCompleteOrIncomplete", "otherReason"],
    "construction": ["constructionStage"],
    "warrantyPeriod": ["warranty", "warrantyIncomplete"],
}

# IO-863 spec op 4 ("Rakentamishankkeet"): construction projects whose detail is
# the old ``firstPhaseComplete`` ("Ensimmäinen vaihe valmis") move BACK to the
# ``constructionWait`` ("Odottaa rakentamista") phase and take the renamed
# ``firstPhaseCompleteOrIncomplete`` ("Ensimmäinen vaihe valmis/keskeneräinen")
# detail. The old detail row is then removed. This is a deliberate phase move
# requested by the customer, not a regression.
REMOVED_CONSTRUCTION_DETAIL = "firstPhaseComplete"
FIRST_PHASE_COMPLETE_TARGET_PHASE = "constructionWait"
FIRST_PHASE_COMPLETE_TARGET_DETAIL = "firstPhaseCompleteOrIncomplete"

# IO-863 spec op 5 ("Takuuajan hankkeet"): every warranty-period project gets the
# ``warranty`` ("Takuuaika") detail.
WARRANTY_PHASE_VALUE = "warrantyPeriod"
WARRANTY_BACKFILL_DETAIL_VALUE = "warranty"

# Details that move to a different (surviving) phase, keeping their value.
# IO-863: ``movedToConstruction`` (relabeled "Siirretty rakennuttamiseen" in the UI)
# moves from ``constructionPreparation`` to ``constructionWait``. Projects currently
# on this detail move with it so phase and phaseDetail stay consistent.
# Format: detail value -> (old phase value, new phase value).
REPARENTED_DETAILS = {
    "movedToConstruction": ("constructionPreparation", "constructionWait"),
}

# Final phase order after the restructure. Position == index == order (0-based,
# matching update-phase-indexes.sql). These are exactly the phases that survive.
TARGET_PHASE_ORDER = [
    "proposal",
    "design",
    "programming",
    "designPlanning",
    "constructionWait",
    "constructionPreparation",
    "construction",
    "warrantyPeriod",
    "completed",
    "suspended",
]
