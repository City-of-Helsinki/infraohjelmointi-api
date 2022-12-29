from django.core.management.base import BaseCommand, CommandError
from infraohjelmointi_api.models import ProjectClass, Project
import requests
import os
from os import path
import urllib3
import pandas as pd
import environ
import numpy as np
from django.db import transaction


requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"
if path.exists(".env"):
    environ.Env().read_env(".env")

env = environ.Env()


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
            help="Optional argument to allow deletion of all data from ProjectClass Table",
        )
        parser.add_argument(
            "--sync-with-pw",
            action="store_true",
            help="Optional argument to sync classes from PW to Projects table in DB",
        )
        parser.add_argument(
            "--populate-with-excel",
            action="store_true",
            help="Optional argument to read data from excel and populate the DB",
        )

    @transaction.atomic
    def populateDB(self, row):
        if row[0] != None:
            masterClass, masterExists = ProjectClass.objects.get_or_create(
                name=row[0], parent=None
            )
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

    @transaction.atomic
    def syncPW(self):
        projects = Project.objects.exclude(hkrId=None)
        session = requests.Session()
        session.auth = (env("PW_USERNAME"), env("PW_PASSWORD"))
        for project in projects:
            response = session.get(
                "https://prokkis.hel.fi/ws/v2.8/repositories/Bentley.PW--HELS000601.helsinki1.hki.local~3APWHKIKOUL/PW_WSG_Dynamic/PrType_1121_HKR_Hankerek_Hanke?$filter=PROJECT_HKRHanketunnus+eq+{}".format(
                    project.hkrId
                )
            )
            if len(response.json()["instances"]) > 0:
                projectProperties = response.json()["instances"][0]["properties"]

                if projectProperties["PROJECT_Pluokka"] != "":
                    try:
                        masterClass = ProjectClass.objects.get(
                            name=projectProperties["PROJECT_Pluokka"]
                        )
                    except ProjectClass.DoesNotExist:
                        masterClass = None
                        self.stdout.write(
                            self.style.ERROR(
                                "Master Class with name: {} does not exist in local DB".format(
                                    projectProperties["PROJECT_Pluokka"]
                                )
                            )
                        )
                    if projectProperties["PROJECT_Alaluokka"] != "":
                        try:
                            _class = ProjectClass.objects.get(
                                name=projectProperties["PROJECT_Luokka"],
                                parent=masterClass,
                            )
                        except ProjectClass.DoesNotExist:
                            _class = None
                            self.stdout.write(
                                self.style.ERROR(
                                    "Class with name: {} and Master Class: {} does not exist in local DB".format(
                                        projectProperties["PROJECT_Luokka"],
                                        projectProperties["PROJECT_Pluokka"],
                                    )
                                )
                            )
                        try:
                            project.projectClass = ProjectClass.objects.get(
                                name=projectProperties["PROJECT_Alaluokka"],
                                parent=_class,
                            )
                            project.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    "Updated projectClass to {} for Project with Id: {}".format(
                                        projectProperties["PROJECT_Alaluokka"],
                                        project.id,
                                    )
                                )
                            )
                        except ProjectClass.DoesNotExist:
                            self.stdout.write(
                                self.style.ERROR(
                                    "Sub Class with name: {} and Parent Class: {} does not exist in local DB".format(
                                        projectProperties["PROJECT_Alaluokka"],
                                        projectProperties["PROJECT_Luokka"],
                                    )
                                )
                            )

                    elif projectProperties["PROJECT_Luokka"] != "":
                        try:
                            project.projectClass = ProjectClass.objects.get(
                                name=projectProperties["PROJECT_Luokka"],
                                parent=masterClass,
                            )
                            project.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    "Updated projectClass to {} for Project with Id: {}".format(
                                        projectProperties["PROJECT_Luokka"],
                                        project.id,
                                    )
                                )
                            )
                        except ProjectClass.DoesNotExist:
                            _class = None
                            self.stdout.write(
                                self.style.ERROR(
                                    "Class with name: {} and Master Class: {} does not exist in local DB".format(
                                        projectProperties["PROJECT_Luokka"],
                                        projectProperties["PROJECT_Pluokka"],
                                    )
                                )
                            )

    def handle(self, *args, **options):
        excelPath = options["path"]
        if options["destroy"]:
            ProjectClass.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Deleted all Classes from the DB"))

        if options["populate_with_excel"]:
            if os.path.isfile(excelPath):
                try:
                    classExcel = pd.read_excel(
                        excelPath, sheet_name="Luokkajaot", header=[0]
                    )

                    if [
                        "PÄÄLUOKKA",
                        "LUOKKA",
                        "ALALUOKKA",
                    ] == classExcel.columns.to_list():
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
                    self.style.ERROR(
                        "Excel file does not exist at {}".format(excelPath)
                    )
                )
        if options["sync_with_pw"]:
            self.syncPW()
