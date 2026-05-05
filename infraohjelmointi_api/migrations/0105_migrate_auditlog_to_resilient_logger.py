"""IO-845 — copy historical AuditLog rows into ResilientLogEntry.

Once Plata's submit_unsent_entries cron runs, this backfilled history will be
shipped to Elastic Cloud alongside fresh entries written by ProjectViewSet's
dual-write. The context shape mirrors the live emit so historical and live
entries are indistinguishable in Elastic, except that migrated rows carry
``orig_entry_id`` / ``orig_created_at`` markers that point back to the old
AuditLog row.
"""
import logging

from django.apps.registry import Apps
from django.db import migrations


BATCH_SIZE = 1000


def _actor_dict(actor):
    if not actor:
        return {}
    full_name = f"{actor.first_name} {actor.last_name}".strip()
    return {
        "name": full_name or actor.username,
        "email": actor.email,
    }


def _target_dict(project):
    if not project:
        return {}
    return {
        "type": "project",
        "id": str(project.id),
        "name": project.name,
    }


def migrate_auditlog_to_resilient_logger(apps: Apps, schema_editor):
    AuditLog = apps.get_model("infraohjelmointi_api", "AuditLog")
    ResilientLogEntry = apps.get_model("resilient_logger", "ResilientLogEntry")

    queryset = AuditLog.objects.select_related("actor", "project").order_by("createdDate")

    batch = []
    for entry in queryset.iterator(chunk_size=BATCH_SIZE):
        actor = entry.actor
        project = entry.project
        target_data = _target_dict(project)

        batch.append(
            ResilientLogEntry(
                is_sent=False,
                level=logging.INFO,
                message=f"{entry.operation} on {target_data.get('name', 'unknown')}",
                context={
                    "actor": _actor_dict(actor),
                    "operation": entry.operation,
                    "target": target_data,
                    "status": entry.status,
                    "old_values": entry.old_values,
                    "new_values": entry.new_values,
                    "endpoint": entry.endpoint,
                    "orig_entry_id": str(entry.id),
                    "orig_created_at": entry.createdDate.isoformat().replace("+00:00", "Z"),
                },
            )
        )

        if len(batch) >= BATCH_SIZE:
            ResilientLogEntry.objects.bulk_create(batch)
            batch = []

    if batch:
        ResilientLogEntry.objects.bulk_create(batch)


class Migration(migrations.Migration):

    dependencies = [
        ("infraohjelmointi_api", "0104_update_person_phone_and_title_as_required"),
        ("resilient_logger", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            migrate_auditlog_to_resilient_logger,
            migrations.RunPython.noop,
        ),
    ]
