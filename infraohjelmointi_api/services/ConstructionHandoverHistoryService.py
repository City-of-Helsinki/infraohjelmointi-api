"""Reconstructs a human-readable change history for a ConstructionHandover.

The handover tracks its own history through `HistoricalModel` (django-simple-
history), but with a custom twist in `HistoricalModel.save()`:

* on **create** the auto-generated `+` record is deleted, so there is no history
  row for the creation itself;
* on each **update** the freshly created row is rewritten to hold the *previous*
  field values, and its `history_user` is set to the editor of that previous
  version.

So the stored rows are snapshots of past states, newest change last. To turn
them into "who changed what, when" events we line the snapshots up oldest→newest
(`records + [live object]`) and compare each adjacent pair. For the pair that
produced snapshot *k* the actor is the user who set snapshot *k* (the next
record's `history_user`, or the live object's `updatedBy` for the latest state)
and the timestamp is when the previous snapshot was superseded (the old record's
`history_date`). The creation event is synthesised from the live object's
`createdBy` / `createdDate`.
"""
from datetime import date as date_cls

# Tracked fields worth surfacing in the UI (the model's history_fields minus the
# bookkeeping `_history_user`). Order is irrelevant; changed_fields is sorted.
HISTORY_FIELDS = [
    "status",
    "name",
    "description",
    "constructionProcurementMethod",
    "constructionStart",
    "constructionEnd",
    "otherTimelineNotes",
    "totalCost",
    "personPlanning",
    "personFinancing",
    "linkDesignDrawings",
    "linkCostAllocation",
    "linkContractBoundaries",
    "constructionProjectManager",
]

# Relations rendered via a person's name.
_PERSON_FIELDS = {"personPlanning", "personFinancing", "constructionProjectManager"}
# Relations rendered via the related row's `value`.
_VALUE_FIELDS = {"constructionProcurementMethod"}
_RELATION_FIELDS = _PERSON_FIELDS | _VALUE_FIELDS


def _person_name(person) -> str | None:
    if person is None:
        return None
    name = "{} {}".format(
        getattr(person, "firstName", "") or "", getattr(person, "lastName", "") or ""
    ).strip()
    return name or None


def _display(field, snapshot):
    """Human-readable value of `field` on a snapshot (history row or live obj)."""
    raw = getattr(snapshot, field, None)
    if raw is None:
        return None
    if field in _PERSON_FIELDS:
        return _person_name(raw)
    if field in _VALUE_FIELDS:
        return getattr(raw, "value", None)
    if isinstance(raw, date_cls):
        return raw.isoformat()
    return str(raw)


def _compare_key(field, snapshot):
    """Stable equality key: FK id for relations (avoids name collisions), else
    the displayed value. Uses `<field>_id` so relations don't hit the DB."""
    if field in _RELATION_FIELDS:
        return getattr(snapshot, field + "_id", None)
    return _display(field, snapshot)


def _actor_payload(user) -> dict:
    if user is None:
        return {
            "actor": None,
            "actor_username": None,
            "actor_first_name": None,
            "actor_last_name": None,
        }
    return {
        "actor": str(getattr(user, "uuid", None) or user.pk),
        "actor_username": getattr(user, "username", None),
        "actor_first_name": getattr(user, "first_name", None),
        "actor_last_name": getattr(user, "last_name", None),
    }


def _event(event_id, operation, actor, when, old_values, new_values) -> dict:
    return {
        "id": event_id,
        **_actor_payload(actor),
        "operation": operation,
        "old_values": old_values,
        "new_values": new_values,
        "changed_fields": sorted(set(old_values) | set(new_values)),
        "createdDate": when.isoformat() if when is not None else None,
    }


def build_history(handover) -> list:
    """Return the handover's change events, newest first."""
    records = list(
        handover.history.all()
        .select_related(
            "personPlanning",
            "personFinancing",
            "constructionProjectManager",
            "constructionProcurementMethod",
        )
        .order_by("history_date", "history_id")
    )
    # Snapshots oldest→newest: each record holds an old state, the live object
    # holds the current one.
    snapshots = records + [handover]

    events = [
        _event(
            event_id="{}:created".format(handover.id),
            operation="CREATE",
            actor=handover.createdBy,
            when=handover.createdDate,
            old_values={},
            new_values={},
        )
    ]

    for k in range(1, len(snapshots)):
        old_snap = snapshots[k - 1]
        new_snap = snapshots[k]
        changed = [
            field
            for field in HISTORY_FIELDS
            if _compare_key(field, old_snap) != _compare_key(field, new_snap)
        ]
        if not changed:
            continue

        old_record = records[k - 1]
        actor = records[k].history_user if k < len(records) else handover.updatedBy
        events.append(
            _event(
                event_id=str(old_record.history_id),
                operation="UPDATE",
                actor=actor,
                when=old_record.history_date,
                old_values={field: _display(field, old_snap) for field in changed},
                new_values={field: _display(field, new_snap) for field in changed},
            )
        )

    # Built oldest→newest (creation first); the UI wants newest first.
    events.reverse()
    return events
