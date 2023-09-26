from django.core.management.base import BaseCommand, CommandError
from .util.hierarchy import buildHierarchies
import os
from openpyxl import load_workbook
from django.db import transaction
import traceback

from ...services import ProjectWiseService


class Command(BaseCommand):
    help = (
        "Populates the DB with correct project class and location hierarchies. "
        + "\nUsage: python manage.py hierarchies --file <path/to/excel.xlsx>"
        + "\n--sync-locations-from-pw"
    )

    def add_arguments(self, parser):
        """
        Add the following arguments to the hierarchies command

        --file /folder/folder/file.xlsx
        --sync-locations-from-pw
        """

        ## --file, used to tell the script to populate local db with
        ## class/location data using the path provided in the --file argument
        parser.add_argument(
            "--file",
            type=str,
            help=(
                "Argument to give full path to the excel file containing Class/Location data. "
                + "Usage: --file /folder/folder/file.xlsx"
            ),
            default="",
        )
        ## --sync-locations-from-pw, used to tell the script to populate local db with
        ## location data from PW

        parser.add_argument(
            "--sync-locations-from-pw",
            action="store_true",
            help=(
                "Argument to give to synchronize all locations from PW into DB. "
                + "Usage: --sync-locations-from-pw"
            ),
        )

    def handle(self, *args, **options):
        if not options["file"] and not options["sync_locations_from_pw"]:
            self.stdout.write(
                self.style.ERROR(
                    "No arguments given. "
                    + "\nUsage: python manage.py hierarchies --file <path/to/excel.xlsx>"
                    + "\n --sync-locations-from-pw"
                )
            )
            return
        if options["sync_locations_from_pw"]:
            ProjectWiseService().fetch_locations()
            return

        if not os.path.isfile(options["file"]):
            self.stdout.write(
                self.style.ERROR(
                    "Excel file path is incorrect or missing. Usage: --file path/to/file.xlsx"
                )
            )
            return

        try:
            self.populateDBWithExcel(excelPath=options["file"])
        except Exception as e:
            traceback.print_stack(e)
            self.stdout.write(self.style.ERROR(e))

    def populateDBWithExcel(self, excelPath):
        self.stdout.write(
            self.style.NOTICE(
                "----------------------------------------------------------------\n"
                + "Populating DB with classes and locations\n"
                + "----------------------------------------------------------------\n"
            )
        )
        wb = load_workbook(excelPath, data_only=True, read_only=True)
        buildHierarchies(
            wb=wb,
            rows=list(wb.worksheets[2].rows),
        )
