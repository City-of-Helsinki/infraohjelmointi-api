from datetime import datetime, timezone
from django.core.management.base import BaseCommand, CommandError

from django.db import transaction
from ...services import SapApiService, SapAuthenticationError


class Command(BaseCommand):
    help = "Synchronize SAP costs after financial statement is locked. " + "\nUsage: python manage.py fetchsapdatabyyear --year <year> [--force-refetch]"

    def add_arguments(self, parser):
        """
        Add the following arguments to the command
        """

        parser.add_argument(
            "--year",
            type=int,
            help="Year to sync",
        )
        parser.add_argument(
            "--force-refetch",
            action="store_true",
            help=(
                "Bypass the SAP freeze to re-fetch and overwrite frozen-year rows "
                "(IO-790). One-off repair for years whose DB rows were written "
                "before a classification fix reached production."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        year = options["year"]
        if not options["year"]:
            self.stdout.write(
                self.style.ERROR(
                    "No arguments given. "
                    + "\nUsage: python manage.py fetchsapdatabyyear --year <year>"
                )
            )
            return
        # Validate that the year is an integer and within a reasonable range
        try:
            year_int = int(year)
            current_year = datetime.now().year
            if year_int < 2000 or year_int > current_year + 1:
                raise ValueError("Year out of valid range.")

        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"Invalid year argument: {year}. Error: {e}"))
            return

        try:
            service = SapApiService()
            if options.get("force_refetch"):
                # Push the freeze gate far into the future so get_costs_and_commitments_by_year
                # goes out to SAP instead of returning the frozen DB row.
                service.sap_freeze_date = datetime(9999, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
                self.stdout.write(
                    self.style.WARNING(
                        f"--force-refetch: bypassing SAP freeze for year {year_int}"
                    )
                )
            service.sync_all_projects_from_sap(for_financial_statement=True, sap_year=year)
        except SapAuthenticationError as e:
            raise CommandError(
                f"SAP authentication failed (401). Fix credentials and retry. {e}"
            ) from e