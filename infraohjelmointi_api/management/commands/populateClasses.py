from django.core.management.base import BaseCommand, CommandError
from infraohjelmointi_api.models import ProjectClass
import os
import pandas as pd
import numpy as np


class Command(BaseCommand):
    help = "Populates the DB with correct project class hierarchy"

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            type=str,
            default="/app/infraohjelmointi_api/mock_data/PW_class_location.xlsx",
        )
        parser.add_argument(
            "--destroy",
            action="store_true",
            help="Deletes all classes from the DB",
        )

    def populateDB(self, row):
        if row[0] != None:
            masterClass, masterExists = ProjectClass.objects.get_or_create(name=row[0])
            if masterExists:
                self.stdout.write(
                    self.style.SUCCESS("Created Master Class: {}".format(row[0]))
                )
            if row[1] != None:
                _class, classExists = masterClass.parentClass.get_or_create(name=row[1])
                if classExists:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Created Class: {} with Master Class: {}".format(
                                row[1], row[0]
                            )
                        )
                    )
                if row[2] != None:
                    _, subClassExists = _class.parentClass.get_or_create(name=row[2])
                    if subClassExists:
                        self.stdout.write(
                            self.style.SUCCESS(
                                "Created Sub Class: {} with Class: {} and Master Class: {} ".format(
                                    row[2], row[1], row[0]
                                )
                            )
                        )

    def handle(self, *args, **options):
        excelPath = options["path"]
        if options["destroy"]:
            ProjectClass.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Deleted all Classes from the DB"))
            return
        if os.path.isfile(excelPath):
            try:
                classExcel = pd.read_excel(
                    excelPath, sheet_name="Luokkajaot", header=[0]
                )
                if ["PÄÄLUOKKA", "LUOKKA", "ALALUOKKA"] == classExcel.columns.to_list():
                    classExcel.replace({np.nan: None}, inplace=True)
                    classExcel.apply(
                        self.populateDB,
                        axis=1,
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            "Excel sheet should have the following columns only PÄÄLUOKKA, LUOKKA, ALALUOKKA"
                        )
                    )

            except Exception as e:
                self.stdout.write(self.style.ERROR(e))

        else:
            self.stdout.write(
                self.style.ERROR("Excel file does not exist at {}".format(excelPath))
            )
