import requests
from os import path
import environ
import re
import logging
import time

from datetime import datetime

logger = logging.getLogger("infraohjelmointi_api")

from ..models import (
    Project,
    Person,
)

from .PersonService import PersonService
from .ProjectService import ProjectService
from .ProjectLocationService import ProjectLocationService

from .utils import ProjectWiseDataMapper, ProjectWiseDataFieldNotFound

env = environ.Env()
env.escape_proxy = True

if path.exists(".env"):
    env.read_env(".env")

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"


class ProjectWiseService:
    def __init__(self) -> None:
        # connection setup
        self.session = requests.Session()
        self.session.auth = (env("PW_USERNAME"), env("PW_PASSWORD"))
        self.pw_api_url = env("PW_API_URL")

        self.pw_api_location_endpoint = env("PW_API_LOCATION_ENDPOINT")
        self.pw_api_project_metadata_endpoint = env("PW_API_PROJECT_META_ENDPOINT")

        self.pw_api_project_update_endpoint = env("PW_PROJECT_UPDATE_ENDPOINT")

        self.project_wise_data_mapper = ProjectWiseDataMapper()

        # preload data from DB to optimize performance
        self.project_phases = self.project_wise_data_mapper.load_and_transform_phases()
        self.project_areas = (
            self.project_wise_data_mapper.load_and_transform_project_areas()
        )
        self.responsible_zones = (
            self.project_wise_data_mapper.load_and_transform_responsible_zones()
        )
        self.construction_phase_details = (
            self.project_wise_data_mapper.load_and_transform_construction_phase_details()
        )
        self.project_types = (
            self.project_wise_data_mapper.load_and_transform_project_types()
        )

    def sync_all_projects_from_pw(self) -> None:
        """Method to synchronise all projects in DB with PW project data.\n"""

        logger.debug("Synchronizing all projects in DB with PW")
        self.sync_projects_from_pw(projects=ProjectService.list_with_non_null_hkr_id())

    def sync_projects_from_pw(self, projects: list[Project]) -> None:
        """Method to synchronise given projects with PW project data.\n
        Given projects must have hkrId otherwise project missing hkrId will not be syncrhonized.
        """

        logger.debug(f"Synchronizing given projects '{len(projects)}' in DB with PW")
        for project in projects:
            self.sync_project_from_pw(project=project)

    def syn_project_from_pw(self, pw_id: str) -> None:
        """Method to synchronise project with given PW id with PW project data.\n"""

        logger.debug(f"Synchronizing given project with PW Id '{pw_id}' with PW")
        self.sync_project_from_pw(ProjectService.get_by_hkr_id(hkr_id=pw_id))

    def sync_project_from_pw(self, project: Project) -> None:
        """Method to synchronise given project from PW project data.\n
        Given project must have hkrId otherwise project will not be syncrhonized.
        """

        logger.debug(
            f"Synchronizing given project '{project.id}' with PW Id '{project.hkrId}' from PW"
        )
        if not project.hkrId:
            return
        try:
            start_time = time.perf_counter()
            # fetch project data from PW
            pw_project = self.get_project_from_pw(project.hkrId)

            # handle the reponse
            self.__proceed_with_pw_project(pw_project=pw_project, project=project)

            handling_time = time.perf_counter() - start_time
            logger.info(
                f"Project {project.id} with successully synchronized from PW in {handling_time}s"
            )
        except (PWProjectNotFoundError, PWProjectResponseError) as e:
            logger.error(e)

    def sync_project_to_pw(self, data: dict, project: Project) -> None:
        """Method to synchronise given product field value to PW"""
        if project.hkrId is None or str(project.hkrId).strip() == "":
            return
        try:
            pw_project_data = self.project_wise_data_mapper.convert_to_pw_data(
                data=data, project=project
            )

            pw_instance_id = self.get_project_from_pw(project.hkrId)[
                "relationshipInstances"
            ][0]["relatedInstance"]["instanceId"]

            (
                schema_name,
                class_name,
                *others,
            ) = self.pw_api_project_update_endpoint.split("/")

            pw_update_data = {
                "instance": {
                    "schemaName": schema_name,
                    "className": class_name,
                    "instanceId": pw_instance_id,
                    "changeState": "modified",
                    "properties": pw_project_data,
                }
            }

            api_url = f"{self.pw_api_url}{self.pw_api_project_update_endpoint}{pw_instance_id}"

            logger.debug(f"PW update endpoint {api_url}")
            logger.debug(f"Update request data: {pw_update_data}")

            response = self.session.post(url=api_url, json=pw_update_data)
            logger.debug("PW responded to Update request")
            logger.debug(response.json())
        except (
            ProjectWiseDataFieldNotFound,
            PWProjectResponseError,
            PWProjectNotFoundError,
        ) as e:
            logger.error(
                f"Error occured while syncing project '{project.id}' to PW with data '{data}'. {e}"
            )

    def get_project_from_pw(self, id: str):
        """Method to fetch project from PW with given PW project id"""
        start_time = time.perf_counter()
        api_url = f"{self.pw_api_url}{self.pw_api_project_metadata_endpoint}{id}"

        logger.debug("Requesting API {}".format(api_url))
        response = self.session.get(api_url)
        response_time = time.perf_counter() - start_time

        logger.debug(f"PW responded in {response_time}s")

        # Check if PW responded with error
        if response.status_code != 200:
            raise PWProjectResponseError(
                f"PW responded with status code '{response.status_code}' and reason '{response.reason}' for given id '{id}'"
            )

        # Check if the project exists on PW
        json_response = response.json()["instances"]
        if len(json_response) == 0:
            raise PWProjectNotFoundError(
                "No project found from PW with given id '{}'".format(id)
            )

        return json_response[0]

    def fetch_locations(self):
        """
        Currently fetches only sub divisions from PW.
        Other locations come from Excel files.
        """
        api_url = f"{self.pw_api_url}{self.pw_api_location_endpoint}"

        logger.debug("Requesting API {}".format(api_url))

        response = self.session.get(api_url)

        # Check if PW responded with error
        if response.status_code != 200:
            raise PWProjectResponseError(
                f"PW responded with status code '{response.status_code}' and reason '{response.reason}' for given id '{id}'"
            )
        locations = response.json()["instances"]
        logger.info(f"PW responded with {len(locations)} locations")

        # Iterate the result received from PW
        for model_data in locations:
            model_data = model_data["properties"]
            district = model_data["PAALUOKKA"].strip().title()
            division = model_data["LUOKKA"].strip().title()
            district_division_path = f"{district}/{division}"

            sub_division = model_data["ALALUOKKA"].strip().title()
            sub_division_path = f"{district_division_path}/{sub_division}"

            if not sub_division:
                logger.error(
                    "Sub division '{}' cannot be handled".format(
                        sub_division, sub_division_path
                    )
                )
                continue

            district_divisions = list(
                ProjectLocationService.find_by_path(path=district_division_path)
            )

            if len(district_divisions) == 0:
                # skip thi record because the district should be found in DB
                logger.error(
                    "No parent location found by path '{}'. Cannot create sub division '{}' with path '{}'".format(
                        district_division_path, sub_division, sub_division_path
                    )
                )
                continue

            sub_divisions = list(
                ProjectLocationService.find_by_path(path=sub_division_path)
            )
            if len(sub_divisions) > 0:
                logger.info(
                    "Sub division '{}' already exists in DB with path '{}'".format(
                        sub_division, sub_division_path
                    )
                )
                continue

            for parent_location in district_divisions:
                try:
                    location, _ = ProjectLocationService.get_or_create(
                        name=sub_division,
                        parent=parent_location,
                        path=sub_division_path,
                        parentClass=parent_location.parentClass,
                    )
                    logger.info(
                        "Sub division '{}' successfully created with '{}'. Its id '{}'".format(
                            sub_division, sub_division_path, location.id
                        )
                    )
                except Exception as e:
                    logger.error(
                        "Error occurred while creating sub division '{}' with path '{}'. \nError: {}".format(
                            sub_division, sub_division_path, e
                        )
                    )

    def __proceed_with_pw_project(self, pw_project, project: Project) -> None:
        """Helper method to handle PW project data and copy it to given project"""

        project_properties = pw_project["relationshipInstances"][0]["relatedInstance"][
            "properties"
        ]
        description = (
            " ".join(project_properties["PROJECT_Hankkeen_kuvaus"].split())
            if project_properties["PROJECT_Hankkeen_kuvaus"]
            else "Kuvaus puuttuu"
        )
        if description != "Kuvaus puuttuu" or description != "":
            project.description = description

        if project_properties["PROJECT_Kadun_tai_puiston_nimi"]:
            project.address = project_properties["PROJECT_Kadun_tai_puiston_nimi"]

        if project_properties["PROJECT_Hankkeen_vaihe"]:
            project.phase = self.project_phases[
                project_properties["PROJECT_Hankkeen_vaihe"]
            ]

        if project_properties["PROJECT_Louheen"]:
            project.louhi = project_properties["PROJECT_Louheen"] != "Ei"

        if project_properties["PROJECT_Sorakatu"]:
            project.gravel = project_properties["PROJECT_Sorakatu"] != "Ei"

        if project_properties["PROJECT_Projektialue"]:
            project.area = self.project_areas[
                project_properties["PROJECT_Projektialue"]
            ]

        if project_properties["PROJECT_Aluekokonaisuuden_nimi"]:
            project.entityName = project_properties["PROJECT_Aluekokonaisuuden_nimi"]

        if project_properties["PROJECT_Ohjelmoitu"]:
            project.programmed = project_properties["PROJECT_Ohjelmoitu"] != "Ei"

        if project_properties["PROJECT_Rakentamisvaiheen_tarkenne"]:
            project.constructionPhaseDetail = self.construction_phase_details[
                project_properties["PROJECT_Rakentamisvaiheen_tarkenne"]
            ]

        if project_properties["PROJECT_Toimiala"]:
            project.type = self.project_types[project_properties["PROJECT_Toimiala"]]

        if project_properties["PROJECT_Alue_rakennusviraston_vastuujaon_mukaan"]:
            project.responsibleZone = self.responsible_zones[
                project_properties["PROJECT_Alue_rakennusviraston_vastuujaon_mukaan"]
            ]

        if project_properties["PROJECT_Louhi__hankkeen_aloitusvuosi"]:
            project.planningStartYear = project_properties[
                "PROJECT_Louhi__hankkeen_aloitusvuosi"
            ]

        if project_properties["PROJECT_Louhi__hankkeen_valmistumisvuosi"]:
            project.constructionEndYear = project_properties[
                "PROJECT_Louhi__hankkeen_valmistumisvuosi"
            ]

        if "PROJECT_Hankkeen_rakentaminen_alkaa" in project_properties:
            project.estConstructionStart = datetime.strptime(
                project_properties["PROJECT_Hankkeen_rakentaminen_alkaa"],
                "%Y-%m-%dT%H:%M:%S",
            )

        if "PROJECT_Hankkeen_rakentaminen_pttyy" in project_properties:
            project.estConstructionEnd = datetime.strptime(
                project_properties["PROJECT_Hankkeen_rakentaminen_pttyy"],
                "%Y-%m-%dT%H:%M:%S",
            )

        if "PROJECT_Nhtvillolo_alku" in project_properties:
            project.visibilityStart = datetime.strptime(
                project_properties["PROJECT_Nhtvillolo_alku"],
                "%Y-%m-%dT%H:%M:%S",
            )

        if "PROJECT_Nhtvillolo_loppu" in project_properties:
            project.visibilityEnd = datetime.strptime(
                project_properties["PROJECT_Nhtvillolo_loppu"],
                "%Y-%m-%dT%H:%M:%S",
            )

        if "PROJECT_Esillaolo_alku" in project_properties:
            project.presenceStart = datetime.strptime(
                project_properties["PROJECT_Esillaolo_alku"],
                "%Y-%m-%dT%H:%M:%S",
            )

        if "PROJECT_Esillaolo_loppu" in project_properties:
            project.presenceEnd = datetime.strptime(
                project_properties["PROJECT_Esillaolo_loppu"],
                "%Y-%m-%dT%H:%M:%S",
            )

        if "PROJECT_Hankkeen_suunnittelu_alkaa" in project_properties:
            project.estPlanningStart = datetime.strptime(
                project_properties["PROJECT_Hankkeen_suunnittelu_alkaa"],
                "%Y-%m-%dT%H:%M:%S",
            )

        if "PROJECT_Hankkeen_suunnittelu_pttyy" in project_properties:
            project.estPlanningEnd = datetime.strptime(
                project_properties["PROJECT_Hankkeen_suunnittelu_pttyy"],
                "%Y-%m-%dT%H:%M:%S",
            )

        if not project.personPlanning:
            planning_person_data = "{}, {}, {}, {}".format(
                project_properties["PROJECT_Vastuuhenkil"],
                project_properties["PROJECT_Vastuuhenkiln_titteli"],
                project_properties["PROJECT_Vastuuhenkiln_puhelinnumero"],
                project_properties["PROJECT_Vastuuhenkiln_shkpostiosoite"],
            )

            planning_person = self.__get_project_person(
                person_data=planning_person_data
            )
            if planning_person:
                project.personPlanning = planning_person

        if project_properties["PROJECT_Vastuuhenkil_rakennuttaminen"]:
            construction_person = self.__get_project_person(
                person_data=project_properties["PROJECT_Vastuuhenkil_rakennuttaminen"]
            )

            if construction_person:
                project.personConstruction = construction_person

        if project_properties["PROJECT_Muut_vastuuhenkilt"]:
            project.otherPersons = self.__get_fav_persons(
                project_properties["PROJECT_Muut_vastuuhenkilt"]
            )

        project.save()

    def __get_project_person(self, person_data: str) -> Person:
        """Helper method to load person from DB with PW data"""

        person_data = person_data.strip().replace(", ", ",")
        if not person_data.rstrip(","):
            return None
        try:
            full_name, title, phone_nr, email = person_data.split(",")
            last_name, first_name = re.split("(?<=.)(?<!\-)(?=[A-Z])", full_name)
            person, _ = PersonService.get_or_create_by_name(
                firstName=first_name.strip().title(), lastName=last_name.strip().title()
            )

            if title:
                person.title = title.strip().title()
            if phone_nr:
                person.phone = phone_nr.strip()
            if email:
                person.email = email.strip()

            person.save()

            return person
        except Exception:
            return None

    def __get_fav_persons(self, person_data: str) -> list[Person]:
        """Helper method to load persons from DB with PW data"""

        person_data = person_data.strip().replace(", ", ",").rstrip(",")
        if not person_data:
            return None
        fav_persons = []
        # Firstname Lastname, Title, phone, email format
        if re.findall(
            "^[a-zA-ZäöåÄÖÅ]+ [a-zA-ZäöåÄÖÅ]+,[a-zA-ZäöåÄÖ\. ]+,[a-zA-ZäöåÄÖÅ0-9\. ]+,[a-zA-ZäöåÄÖÅ@\.]+$",
            person_data,
        ):
            fav_persons.append(self.__get_project_person(person_data=person_data))
            return fav_persons

        for person in person_data.split(","):
            # FirstnameLastname or Firstname Lastname
            fav_person_data = re.split("(?<=.)(?=[A-Z])", person)
            if len(fav_person_data) == 1:
                # email format?
                fav_person_data = re.split("\\.|@", person)
            if len(fav_person_data) == 1:
                # just one string so add an empty value to list
                fav_person_data.append(" ")

            fav_person = self.__get_project_person(
                fav_person_data[1] + " " + fav_person_data[0] + ",,,"
            )
            if fav_person:
                fav_persons.append(fav_person)
        return fav_persons


class PWProjectNotFoundError(RuntimeError):
    """Error representing not found project in PW error"""

    pass


class PWProjectResponseError(RuntimeError):
    """Error representing PW error with non status code of 200"""

    pass
