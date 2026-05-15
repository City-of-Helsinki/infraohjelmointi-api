"""IO-865: list programmed projects whose hkrId is missing from ProjectWise.

CSV columns on stdout: id,name,hkrId,reason
Reason is "not_found" or "pw_response_error".

Exit code is a bitmask so monitoring can tell a data issue from a PW outage:

  0  clean
  1  one or more orphans found (data action needed)
  2  one or more PW response errors (PW outage / infra alert)
  3  both of the above

Schedulers can therefore page on "exit_code & 2" for infra and on
"exit_code & 1" for data-cleanup workflows.
"""

import argparse
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


EXIT_ORPHANS_FOUND = 1
EXIT_PW_ERRORS = 2


def _positive_int(value: str) -> int:
    ivalue = int(value)
    if ivalue < 1:
        raise argparse.ArgumentTypeError(
            f"--limit must be a positive integer (got {ivalue})"
        )
    return ivalue


class Command(BaseCommand):
    help = (
        "List programmed projects whose hkrId is missing from ProjectWise "
        "(IO-865). Exit code: 1=orphans, 2=PW errors, 3=both."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=_positive_int,
            default=None,
            help="Only check the first N candidate projects. Must be >= 1.",
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

        exit_code = 0
        if orphan_count > 0:
            exit_code |= EXIT_ORPHANS_FOUND
        if error_count > 0:
            exit_code |= EXIT_PW_ERRORS
        if exit_code:
            sys.exit(exit_code)
