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
    help = "Populates the DB with correct project class hierarchy. Usage: python manage.py manageclasses <arguments>"

    def add_arguments(self, parser):
        """
        Adds the following arguments to the manageclasses command

        --path <path/to/excel.xlsx>
        --populate-with-excel
        --sync-with-pw
        """

        ## --path argument, used to provide the path to excel file which contains class data, must give full path
        parser.add_argument(
            "path",
            nargs="?",
            type=str,
            default="/app/infraohjelmointi_api/mock_data/PW_class_location.xlsx",
        )
        ## --sync-with-pw argument, used to tell the script to fetch classes for each project
        ## from PW and assign them classes as defined in PW
        parser.add_argument(
            "--sync-with-pw",
            action="store_true",
            help="Optional argument to sync classes from PW to Projects table in DB",
        )
        ## --populate-with-excel, used to tell the script to populate local db with
        ## class data using the path provided in the --path argument
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
        # Masterclass -> Class -> Subclass
        # Each -> above tells that the next class has the previous class as parent
        if row[0] != None:
            masterClass, masterExists = ProjectClass.objects.get_or_create(
                name=row[0], parent=None, path=row[0]
            )
            if masterExists:
                self.stdout.write(
                    self.style.SUCCESS("Created Master Class: {}".format(row[0]))
                )
            if row[1] != None:
                _class, classExists = masterClass.childClass.get_or_create(
                    name=row[1], path="{}/{}".format(row[0], row[1])
                )
                if classExists:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Created Class: {} with Master Class: {}".format(
                                row[1], row[0]
                            )
                        )
                    )
                if row[2] != None:
                    _, subClassExists = _class.childClass.get_or_create(
                        name=row[2], path="{}/{}/{}".format(row[0], row[1], row[2])
                    )
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
        """
        Function used to loop through projects in local DB and fetch their class data from PW
        @transaction.atomic decorator used so that if any error occurs, the whole
        transaction rollsback any db changes
        """

        # Get all projects from DB with hkrId != None
        projects = Project.objects.exclude(hkrId=None)
        session = requests.Session()
        session.auth = (env("PW_USERNAME"), env("PW_PASSWORD"))
        for project in projects:
            # Fetch PW data for each project, filtered by hkrId
            response = session.get(
                env("PW_TEST_URL")
                + "?$filter=PROJECT_HKRHanketunnus+eq+{}".format(project.hkrId)
            )
            # Check if the project exists on PW
            if len(response.json()["instances"]) > 0:
                projectProperties = response.json()["instances"][0]["properties"]
                # PROJECT_Pluokka = MasterClas
                # PROJECT_Luokka = Class
                # PROJECT_Alaluokka = Subclass
                # First MasterClass is checked to exist on PW, if it exists, then Subclass is checked.
                # If subclass exists, that confirms that class also exists and the subclass is assigned to the project.
                # If Masterclass exists and subclass does not exist, then Class is checked, if class exists then it is assigned to the project
                # A project cannot be assigned only a Masterclass hence if master class does not exist, nothing is assigned to project

                # Check if MasterClass exists on PW
                if projectProperties["PROJECT_Pluokka"] != "":
                    # Try getting the same Masterclass from local DB
                    try:
                        masterClass = ProjectClass.objects.get(
                            name=projectProperties["PROJECT_Pluokka"], parent=None
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
                        continue
                    # Check if SubClass exists after checking for Masterclass
                    if projectProperties["PROJECT_Alaluokka"] != "":
                        # Subclass exists so class should exists in local DB to move forward
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
                            continue
                        # Class exists and now the child subclass can be fetched from DB and assigned to project
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
                            continue
                    # Check if Class exists when SubClass does not exist
                    elif projectProperties["PROJECT_Luokka"] != "":
                        # Fetch Class from local DB given MasterClass as parent
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
                            continue

    def handle(self, *args, **options):
        excelPath = options["path"]

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
