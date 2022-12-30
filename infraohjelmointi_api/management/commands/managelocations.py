from django.core.management.base import BaseCommand
from infraohjelmointi_api.models import ProjectLocation, Project
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
    help = "Populates the DB with correct project class hierarchy. Usage: python manage.py managelocations <arguments>"

    def add_arguments(self, parser):
        """
        Adds the following arguments to the managelocations command

        --path <path/to/excel.xlsx>
        --populate-with-excel
        --sync-with-pw
        """
        ## --path argument, used to provide the path to excel file which contains location data, must give full path
        parser.add_argument(
            "--file",
            type=str,
            help="Argument to give full path to the excel file containing Location data, Usage: --file /folder/foler/file.xlsx",
            default="",
        )
        ## --sync-with-pw argument, used to tell the script to fetch classes for each project
        ## from PW and assign them locations as defined in PW
        parser.add_argument(
            "--sync-with-pw",
            action="store_true",
            help="Optional argument to sync locations from PW to Projects table in DB",
        )
        ## --populate-with-excel, used to tell the script to populate local db with
        ## location data using the path provided in the --path argument
        parser.add_argument(
            "--populate-with-excel",
            action="store_true",
            help="Optional argument to read data from excel and populate the DB",
        )

    @transaction.atomic
    def populateDB(self, row):
        """
        Function used to populate the DB by looping through each row of excel data
        @transaction.atomic decorator used so that if any error occurs, the whole
        transaction rollsback any db changes
        """

        # DB populated in the following order
        # mainDistrict ->  district -> SubDistrict
        # Each -> above tells that the next district has the previous district as parent
        if row[0] != None:
            mainDistrict, mainExists = ProjectLocation.objects.get_or_create(
                name=row[0], parent=None
            )
            if mainExists:
                self.stdout.write(
                    self.style.SUCCESS("Created Main District: {}".format(row[0]))
                )
            if row[1] != None:
                district, districtExists = mainDistrict.childLocation.get_or_create(
                    name=row[1]
                )
                if districtExists:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Created District: {} with Main District: {}".format(
                                row[1], row[0]
                            )
                        )
                    )
                if row[2] != None:
                    _, subDistrictExists = district.childLocation.get_or_create(
                        name=row[2]
                    )
                    if subDistrictExists:
                        self.stdout.write(
                            self.style.SUCCESS(
                                "Created Sub District: {} with District: {} and Main District: {} ".format(
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

                if projectProperties["PROJECT_Suurpiirin_nimi"] != "":
                    try:
                        mainDistrict = ProjectLocation.objects.get(
                            name=projectProperties["PROJECT_Suurpiirin_nimi"]
                        )
                    except ProjectLocation.DoesNotExist:
                        mainDistrict = None
                        self.stdout.write(
                            self.style.ERROR(
                                "Main District with name: {} does not exist in local DB".format(
                                    projectProperties["PROJECT_Suurpiirin_nimi"]
                                )
                            )
                        )

                    if projectProperties["PROJECT_Osa_alue"] != "":
                        try:
                            district = ProjectLocation.objects.get(
                                name=projectProperties["PROJECT_Kaupunginosan_nimi"],
                                parent=mainDistrict,
                            )
                        except ProjectLocation.DoesNotExist:
                            district = None
                            self.stdout.write(
                                self.style.ERROR(
                                    "District with name: {} and Parent: {} does not exist in local DB".format(
                                        projectProperties["PROJECT_Kaupunginosan_nimi"],
                                        projectProperties["PROJECT_Suurpiirin_nimi"],
                                    )
                                )
                            )
                        try:

                            project.projectLocation = ProjectLocation.objects.get(
                                name=projectProperties["PROJECT_Osa_alue"],
                                parent=district,
                            )
                            project.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    "Updated projectLocation to {} for Project with Id: {}".format(
                                        projectProperties["PROJECT_Osa_alue"],
                                        project.id,
                                    )
                                )
                            )
                        except ProjectLocation.DoesNotExist:
                            self.stdout.write(
                                self.style.ERROR(
                                    "Sub District with name: {} and parent: {} does not exist in local DB".format(
                                        projectProperties["PROJECT_Osa_alue"],
                                        projectProperties["PROJECT_Kaupunginosan_nimi"],
                                    )
                                )
                            )
                    elif projectProperties["PROJECT_Kaupunginosan_nimi"] != "":
                        try:
                            project.projectLocation = ProjectLocation.objects.get(
                                name=projectProperties["PROJECT_Kaupunginosan_nimi"],
                                parent=mainDistrict,
                            )
                            project.save()
                            self.stdout.write(
                                self.style.SUCCESS(
                                    "Updated projectClass to {} for Project with Id: {}".format(
                                        projectProperties["PROJECT_Kaupunginosan_nimi"],
                                        project.id,
                                    )
                                )
                            )
                        except ProjectLocation.DoesNotExist:
                            self.stdout.write(
                                self.style.ERROR(
                                    "District with name: {} and parent: {} does not exist in local DB".format(
                                        projectProperties["PROJECT_Kaupunginosan_nimi"],
                                        projectProperties["PROJECT_Suurpiirin_nimi"],
                                    )
                                )
                            )

    def handle(self, *args, **options):
        excelPath = options["path"]
        if options["populate_with_excel"]:
            if os.path.isfile(excelPath):
                try:
                    classExcel = pd.read_excel(
                        excelPath, sheet_name="Aluejaot", header=[0]
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
                        "Excel file does not exist in local DB at {}".format(excelPath)
                    )
                )
        if options["sync_with_pw"]:
            self.syncPW()
