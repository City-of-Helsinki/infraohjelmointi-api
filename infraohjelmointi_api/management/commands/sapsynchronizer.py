from django.core.management.base import BaseCommand, CommandError

from django.db import transaction
from ...services import ProjectService
from ...services import SapApiService


class Command(BaseCommand):
    help = (
        "Synchronize SAP costs. "
        "\nUsage: python manage.py sapsynchronizer"
        "\nUse --counts-only to print project/group/sap_id counts and exit (no SAP/DB writes)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--counts-only",
            action="store_true",
            help="Only print how many projects, groups and SAP IDs would be synced; do not call SAP or write to DB.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options.get("counts_only"):
            self._print_counts_only()
            return
        SapApiService().sync_all_projects_from_sap(for_financial_statement=False)

    def _print_counts_only(self):
        """Load projects, group by SAP ID, print counts. No SAP calls, no DB writes."""
        projects = ProjectService.list_with_non_null_sap_id()
        project_count = projects.count() if hasattr(projects, "count") else len(projects)
        service = SapApiService()
        grouped = service._SapApiService__group_projects_by_sap_id(projects=projects)
        group_count = len(grouped)
        sap_id_count = sum(len(by_sap) for by_sap in grouped.values())
        self.stdout.write(f"Projects with SAP ID: {project_count}")
        self.stdout.write(f"Groups: {group_count}")
        self.stdout.write(f"SAP IDs to process: {sap_id_count}")
        for i, (group_id, by_sap) in enumerate(list(grouped.items())[:5]):
            sap_ids = list(by_sap.keys())[:3]
            self.stdout.write(f"  group {group_id!r}: {len(by_sap)} SAP IDs, first: {sap_ids}")
        if group_count > 5:
            self.stdout.write(f"  ... and {group_count - 5} more groups")
