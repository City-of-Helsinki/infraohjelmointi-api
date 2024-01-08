from django.core.management.base import BaseCommand

import os
import traceback
from openpyxl import load_workbook
from .util.locationFileHandler import addLocations


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help=(
                "Argument to give full path to the excel file containing location data. "
                + "Usage: --file /folder/folder/file.xlsx"
            ),
            default="",
        )

    def handle(self, *args, **options):
        if not options["file"]:
            self.stdout.write(
                self.style.ERROR(
                    "No arguments given. "
                    + "\nUsage: python manage.py locationimporter --file <path/to/excel.xlsx>"
                )
            )
            return
        if not os.path.isfile(options["file"]):
            self.stdout.write(
                self.style.ERROR(
                    "Excel file path is incorrect or missing. Usage: --file path/to/file.xlsx"
                )
            )
            return
        
        try:
            self.populateDBWithLocations(excelPath=options["file"])
        except Exception as e:
            traceback.print_stack(e)
            self.stdout.write(self.style.ERROR(e))

    def populateDBWithLocations(self, excelPath):
        self.stdout.write(
            self.style.NOTICE(
                "\n"
                + '\033[94m'
                + "----------------------------------------------------------------\n"
                + "                 Populating DB with locations                   \n"
                + "----------------------------------------------------------------\n"
                +  '\033[0m'
            )
        )
        wb = load_workbook(excelPath, data_only=True, read_only=True)
        addLocations(list(wb.worksheets[0].rows))