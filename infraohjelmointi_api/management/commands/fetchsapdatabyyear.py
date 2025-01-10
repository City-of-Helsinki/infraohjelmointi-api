from datetime import datetime
from django.core.management.base import BaseCommand, CommandError

from django.db import transaction
from ...services import SapApiService


class Command(BaseCommand):
    help = "Synchronize SAP costs after financial statement is locked. " + "\nUsage: python manage.py fetchsapdatabyyear"

    def add_arguments(self, parser):
        """
        Add the following arguments to the command
        """

        parser.add_argument(
            "--year",
            type=int,
            help="Year to sync",
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
        
        SapApiService().sync_all_projects_from_sap(forFinancialStatement=True, sap_year=year)