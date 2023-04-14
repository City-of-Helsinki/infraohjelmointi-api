from django.core.management.base import BaseCommand, CommandError
from infraohjelmointi_api.models import (
    ProjectClass,
    Project,
    ProjectLocation,
    ResponsibleZone,
)
import requests
import os
from os import path
import urllib3
import pandas as pd
import environ
import numpy as np
from django.db import transaction

from .util.hierarchy import (
    buildHierarchyWithExcelRow,
    getMasterHierarchyModel,
    setSubHierarchyModelToProject,
    setHierarchyModelToProject,
)


requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"
if path.exists(".env"):
    environ.Env().read_env(".env")

env = environ.Env()


class Command(BaseCommand):
    help = (
        "Populates the DB with correct project class hierarchy. "
        + "\nUsage: python manage.py manageclasses --file <path/to/excel.xlsx>"
        + " --populate-with-excel [--sync-with-pw]"
        + "\nOr just: python manage.py manageclasses --sync-with-pw"
    )

    def add_arguments(self, parser):
        """
        Add the following arguments to the manageclasses command

        --file <path/to/excel.xlsx>
        --populate-with-excel
        --sync-with-pw
        """

        ## --file argument, used to provide the path to excel file which contains class data, must give full path
        parser.add_argument(
            "--file",
            type=str,
            help=(
                "Argument to give full path to the excel file containing Class data. "
                + "Usage: --file /folder/folder/file.xlsx"
            ),
            default="",
        )
        ## --sync-with-pw argument, used to tell the script to fetch classes for each project
        ## from PW and assign them classes as defined in PW
        parser.add_argument(
            "--sync-with-pw",
            action="store_true",
            help="Optional argument to sync classes from PW to Projects table in DB",
        )
        ## --populate-with-excel, used to tell the script to populate local db with
        ## class data using the path provided in the --file argument
        parser.add_argument(
            "--populate-with-excel",
            action="store_true",
            help="Optional argument to read data from excel and populate the DB",
        )

    def populateDBWithExcel(self, excelPath):
        self.stdout.write(
            self.style.NOTICE(
                "----------------------------------------------------------------\n"
                + "Populating DB with classes\n"
                + "----------------------------------------------------------------\n"
            )
        )
        classExcel = pd.read_excel(excelPath, sheet_name="Luokkajaot", header=[0])
        self.populateDBWithExcelSheet(classExcel, self.populateDBWithClasses)
        self.stdout.write(
            self.style.NOTICE(
                "----------------------------------------------------------------\n"
                + "Populating DB with locations\n"
                + "----------------------------------------------------------------\n"
            )
        )
        locationExcel = pd.read_excel(excelPath, sheet_name="Aluejaot", header=[0])
        self.populateDBWithExcelSheet(locationExcel, self.populateDBWithLocations)

    def populateDBWithExcelSheet(self, excelData, handler):
        if [
            "PÄÄLUOKKA",
            "LUOKKA",
            "ALALUOKKA",
        ] == excelData.columns.to_list():
            excelData.replace({np.nan: None}, inplace=True)
            excelData.apply(
                handler,
                axis=1,
            )

        else:
            self.stdout.write(
                self.style.ERROR(
                    "Excel sheet should have the following columns only PÄÄLUOKKA, LUOKKA, ALALUOKKA"
                )
            )

    # python manage.py manageclasses --populate-with-excel --file infraohjelmointi_api/mock_data/PW_class_location.xlsx
    @transaction.atomic
    def populateDBWithClasses(self, row):
        buildHierarchyWithExcelRow(ProjectClass, row, self.stdout, self.style)

    @transaction.atomic
    def populateDBWithLocations(self, row):
        buildHierarchyWithExcelRow(ProjectLocation, row, self.stdout, self.style)

    def proceedWithProjectClasses(self, project: Project, projectProperties):
        """
        PROJECT_Pluokka = Master Clas
        PROJECT_Luokka = Class
        PROJECT_Alaluokka = Subclass
        1. Check whether MasterClass exists in projectProperties (PW data) and local DB
        2. If Master Class present, the try to set Subclass to project
        3. Otherwise try to set Class to project
        """
        # 1. Check if MasterClass exists in PW and local DB
        masterClass = getMasterHierarchyModel(
            projectProperties=projectProperties,
            masterHierarchyModelName="PROJECT_Pluokka",
            modelClass=ProjectClass,
            stdout=self.stdout,
            style=self.style,
        )
        if masterClass != None:
            # 2. Try to set Subclass to project
            if setSubHierarchyModelToProject(
                projectProperties=projectProperties,
                hierarchyModelName="PROJECT_Luokka",
                subHierarchyModelName="PROJECT_Alaluokka",
                modelClass=ProjectClass,
                parent=masterClass,
                project=project,
                stdout=self.stdout,
                style=self.style,
            ):
                """Do nothing here"""

            else:  # 3. no Subclass set to project, so try to set Class to project instead
                setHierarchyModelToProject(
                    projectProperties=projectProperties,
                    hierarchyModelName="PROJECT_Luokka",
                    modelClass=ProjectClass,
                    parent=masterClass,
                    project=project,
                    stdout=self.stdout,
                    style=self.style,
                )

    def proceedWithProjectLocations(self, project: Project, projectProperties):
        """
        PROJECT_Suurpiirin_nimi = Master District
        PROJECT_Kaupunginosan_nimi = District
        PROJECT_Osa_alue = Sub District
        1. Check whether Master District exists in projectProperties (PW data) and local DB
        2. If Master District present, the try to set Sub District to project
        3. Otherwise try to set District to project
        """
        # 1. Check if Master District exists in PW and local DB
        masterLocation = getMasterHierarchyModel(
            projectProperties=projectProperties,
            masterHierarchyModelName="PROJECT_Suurpiirin_nimi",
            modelClass=ProjectLocation,
            stdout=self.stdout,
            style=self.style,
        )
        if masterLocation != None:
            # 2. Try to set Sub Ditrict to project
            if setSubHierarchyModelToProject(
                projectProperties=projectProperties,
                hierarchyModelName="PROJECT_Kaupunginosan_nimi",
                subHierarchyModelName="PROJECT_Osa_alue",
                modelClass=ProjectLocation,
                parent=masterLocation,
                project=project,
                stdout=self.stdout,
                style=self.style,
            ):
                """Do nothing here"""

            else:  # 3. no Sub District set to project, so try to set District to project instead
                setHierarchyModelToProject(
                    projectProperties=projectProperties,
                    hierarchyModelName="PROJECT_Kaupunginosan_nimi",
                    modelClass=ProjectLocation,
                    parent=masterLocation,
                    project=project,
                    stdout=self.stdout,
                    style=self.style,
                )

    def proceedWithProjectResponsibleZone(
        self,
        project: Project,
        projectProperties,
        responsibleZonesMap: dict,
    ):
        if (
            not "PROJECT_Alue_rakennusviraston_vastuujaon_mukaan" in projectProperties
            or projectProperties["PROJECT_Alue_rakennusviraston_vastuujaon_mukaan"]
            == ""
        ):
            self.stdout.write(
                self.style.ERROR(
                    "Project '{}' in PW has no responsible zone".format(
                        project.id,
                    )
                )
            )
            return

        responsibleZone = projectProperties[
            "PROJECT_Alue_rakennusviraston_vastuujaon_mukaan"
        ].capitalize()
        if not responsibleZone in responsibleZonesMap:
            self.stdout.write(
                self.style.ERROR(
                    "Uknown responsible zone '{}' receieved from ProjectWise for project '{}'".format(
                        responsibleZone,
                        project.id,
                    )
                )
            )
            return

        mappedResponsibleZone = responsibleZonesMap[responsibleZone]
        setattr(project, "responsibleZone", mappedResponsibleZone)
        project.save()

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
        # load responsible zones from db
        responsibleZones = {rz.value: rz for rz in ResponsibleZone.objects.all()}
        # acceptable zones
        responsibleZonesMap = {
            "Pohjoinen": responsibleZones["north"],
            "Itä": responsibleZones["east"],
            "Länsi": responsibleZones["west"],
        }

        pw_api_url = env("PW_API_URL")
        for project in projects:
            # Fetch PW data for each project, filtered by hkrId
            try:
                response = session.get(
                    pw_api_url
                    + "?$filter=PROJECT_HKRHanketunnus+eq+{}".format(project.hkrId)
                )

                # Check if PW responded with error
                if response.status_code != 200:
                    self.stdout.write(self.style.ERROR(response.json()))
                    continue

                # Check if the project exists on PW
                if len(response.json()["instances"]) == 0:
                    continue

                projectProperties = response.json()["instances"][0]["properties"]

                self.proceedWithProjectClasses(
                    project=project, projectProperties=projectProperties
                )

                self.proceedWithProjectLocations(
                    project=project, projectProperties=projectProperties
                )

                self.proceedWithProjectResponsibleZone(
                    project=project,
                    projectProperties=projectProperties,
                    responsibleZonesMap=responsibleZonesMap,
                )

            except Exception as e:
                self.stdout.write(self.style.ERROR(e))

    def handle(self, *args, **options):
        if (
            not options["file"]
            and not options["populate_with_excel"]
            and not options["sync_with_pw"]
        ):
            self.stdout.write(
                self.style.ERROR(
                    "No arguments given. "
                    + "\nUsage: python manage.py manageclasses --file <path/to/excel.xlsx>"
                    + " --populate-with-excel [--sync-with-pw]"
                    + "\nOr just: python manage.py manageclasses --sync-with-pw"
                )
            )
            return

        excelPath = options["file"]

        if options["populate_with_excel"]:
            if not os.path.isfile(excelPath):
                self.stdout.write(
                    self.style.ERROR(
                        "Excel file path is incorrect or missing. Usage: --file path/to/file.xlsx"
                    )
                )
                return

            try:
                self.populateDBWithExcel(excelPath=excelPath)

            except Exception as e:
                self.stdout.write(self.style.ERROR(e))

        if options["sync_with_pw"]:
            self.syncPW()
