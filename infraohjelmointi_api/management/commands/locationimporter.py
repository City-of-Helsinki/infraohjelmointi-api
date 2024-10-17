from django.core.management.base import BaseCommand

import os
import traceback
from openpyxl import load_workbook

from infraohjelmointi_api.models import ProjectDistrict
from infraohjelmointi_api.services import ProjectDistrictService
from .util.locationFileHandler import add_locations


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
        parser.add_argument(
            "--eri-kaupunginosia",
            action="store_true",
        )
        parser.add_argument(
            "--eri-suurpiirejä",
            action="store_true",
        )

    def handle(self, *args, **options):
        if not options["file"] and not options["eri_kaupunginosia"] and not options["eri_suurpiirejä"]:
            self.stdout.write(
                self.style.ERROR(
                    "No arguments given. "
                    + "\nUsage: python manage.py locationimporter --file <path/to/excel.xlsx>"
                )
            )
            return
        if options["eri_kaupunginosia"] is True:
            self.add_eri_kaupunginosia_location_option()
            return
        
        if options["eri_suurpiirejä"] is True:
            self.add_eri_suurpiirejä_location_option()
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
        add_locations(list(wb.worksheets[0].rows))

    def add_eri_kaupunginosia_location_option(self):
        districts = ProjectDistrict.objects.filter(level='district')
        for district in districts:
            division = ProjectDistrictService.get_or_create(
                name='Eri kaupunginosia',
                parent=district,
                path=district.name + '/Eri kaupunginosia',
                level="division",
                )[0]
            self.stdout.write(
                self.style.NOTICE(division.name + " division was added under " + district.name + " district")
            )

    def add_eri_suurpiirejä_location_option(self):
        division = ProjectDistrictService.get_or_create(
            name='Eri suurpiirejä',
            path='Eri suurpiirejä',
            parent=None,
            level="district",
            )[0]
        self.stdout.write(
            self.style.NOTICE(division.name + " district was added")
        )
