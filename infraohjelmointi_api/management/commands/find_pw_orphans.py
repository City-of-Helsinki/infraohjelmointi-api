"""IO-865: list programmed projects whose hkrId is missing from ProjectWise.

CSV columns on stdout: id,name,hkrId,reason
Reason is "not_found" or "pw_response_error".
Exit code 1 if any orphans were found (so it can drive periodic alerts).
"""

import csv
import logging
import sys

from django.core.management.base import BaseCommand

from infraohjelmointi_api.models import Project
from infraohjelmointi_api.services import ProjectWiseService
from infraohjelmointi_api.services.ProjectWiseService import (
    PWProjectNotFoundError,
    PWProjectResponseError,
)

logger = logging.getLogger("infraohjelmointi_api")


class Command(BaseCommand):
    help = (
        "List programmed projects whose hkrId is missing from ProjectWise "
        "(IO-851)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Only check the first N candidate projects.",
        )

    def handle(self, *args, **options):
        limit = options.get("limit")

        candidates = (
            Project.objects.filter(programmed=True)
            .exclude(hkrId__isnull=True)
            .order_by("name")
        )
        if limit is not None:
            candidates = candidates[:limit]

        pw_service = ProjectWiseService()

        writer = csv.writer(self.stdout)
        writer.writerow(["id", "name", "hkrId", "reason"])

        ok_count = 0
        orphan_count = 0
        error_count = 0

        for project in candidates.iterator():
            try:
                pw_service.get_project_from_pw(project.hkrId)
                ok_count += 1
            except PWProjectNotFoundError:
                orphan_count += 1
                writer.writerow([project.id, project.name, project.hkrId, "not_found"])
            except PWProjectResponseError as exc:
                error_count += 1
                writer.writerow(
                    [project.id, project.name, project.hkrId, "pw_response_error"]
                )
                logger.warning(
                    "find_pw_orphans: PW response error for %s (HKR %s): %s",
                    project.name,
                    project.hkrId,
                    exc,
                )

        summary = (
            f"# checked={ok_count + orphan_count + error_count} "
            f"ok={ok_count} orphans={orphan_count} pw_errors={error_count}"
        )
        self.stderr.write(summary)

        if orphan_count > 0:
            sys.exit(1)
