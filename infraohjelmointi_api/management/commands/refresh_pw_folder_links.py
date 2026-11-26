import logging
import requests
from django.core.management.base import BaseCommand, CommandError

from infraohjelmointi_api.models import Project, ProjectWiseFolder
from infraohjelmointi_api.services import ProjectWiseService
from infraohjelmointi_api.services.ProjectWiseService import (
    PWProjectNotFoundError,
    PWProjectResponseError,
)

logger = logging.getLogger("infraohjelmointi_api")


class Command(BaseCommand):
    help = "Refresh ProjectWise folder identifiers for the external API."

    def handle(self, *args, **options):
        hkr_ids = (
            Project.objects.exclude(hkrId__isnull=True)
            .order_by("hkrId")
            .values_list("hkrId", flat=True)
            .distinct()
        )
        service = ProjectWiseService()
        updated = missing = failed = 0
        for hkr_id in hkr_ids.iterator():
            try:
                pw_project = service.get_project_from_pw(
                    hkr_id, timeout=service.PW_NAME_LOOKUP_TIMEOUT_SECONDS
                )
                instance_id = pw_project.get("instanceId")
                if not isinstance(instance_id, str) or not instance_id.strip() or len(instance_id) > 256:
                    raise PWProjectResponseError("PW project has no valid folder instanceId")
                ProjectWiseFolder.objects.update_or_create(
                    hkrId=hkr_id, defaults={"instanceId": instance_id}
                )
                updated += 1
            except PWProjectNotFoundError:
                ProjectWiseFolder.objects.filter(hkrId=hkr_id).delete()
                missing += 1
            except (PWProjectResponseError, requests.RequestException, ValueError, KeyError, TypeError, AttributeError) as exc:
                failed += 1
                logger.warning("ProjectWise folder refresh failed for HKR %s: %s", hkr_id, exc)

        self.stdout.write(f"updated={updated} missing={missing} failed={failed}")
        if failed:
            raise CommandError("ProjectWise folder refresh failed for one or more projects")