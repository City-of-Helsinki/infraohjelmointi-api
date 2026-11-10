import logging

from django.core.management.base import BaseCommand

from infraohjelmointi_api.services.PersonalDataRetentionService import overdue_projects

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Report projects whose personal data is past the five-year retention period. "
        "Read-only: an admin confirms each removal in the admin view."
    )

    def handle(self, *args, **options):
        overdue = overdue_projects()
        if not overdue:
            self.stdout.write("No projects past personal data retention.")
            return

        project_ids = [str(project.id) for project, _ in overdue]
        message = (
            f"{len(overdue)} project(s) past personal data retention await admin confirmation: "
            + ", ".join(project_ids)
        )
        logger.warning(message)
        self.stdout.write(message)
