import requests
from os import path
import environ
import re
import logging
import time

logger = logging.getLogger("infraohjelmointi_api")

from ..models import (
    Project,
    Person,
)

from .PersonService import PersonService
from .ProjectTypeService import ProjectTypeService
from .ProjectService import ProjectService
from .ProjectPhaseService import ProjectPhaseService
from .ProjectAreaService import ProjectAreaService
from .ResponsibleZoneService import ResponsibleZoneService
from .ConstructionPhaseDetailService import ConstructionPhaseDetailService

if path.exists(".env"):
    environ.Env().read_env(".env")

env = environ.Env()
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"


class ProjectWiseService:
    def __init__(self) -> None:
        # connection setup
        self.session = requests.Session()
        self.session.auth = (env("PW_USERNAME"), env("PW_PASSWORD"))
        self.pw_api_url = env("PW_API_URL")
        self.pw_api_project_endpoint = env("PW_API_PROJECT_ENDPOINT")

        # preload data from DB to optimize performance
        self.project_phases = self.__load_and_transform_phases()
        self.project_areas = self.__load_and_transform_project_areas()
        self.responsible_zones = self.__load_and_transform_responsible_zones()
        self.construction_phase_details = (
            self.__load_and_transform_construction_phase_details()
        )
        self.project_types = self.__load_and_transform_project_types()

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
        """Method to synchronise given project with PW project data.\n
        Given project must have hkrId otherwise project will not be syncrhonized.
        """

        logger.debug(
            f"Synchronizing given project '{project.id}' with PW Id '{project.hkrId}' with PW"
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
                f"Project {project.id} with successully synchronized with PW in {handling_time}s"
            )
        except PWProjectNotFoundError as e:
            logger.error(e)
        except PWProjectResponseError as e:
            logger.error(e)

    def get_project_from_pw(self, id: str):
        """Method to fetch project from PW with given PW project id"""
        start_time = time.perf_counter()
        response = self.session.get(
            f"{self.pw_api_url}{self.pw_api_project_endpoint}+{id}"
        )
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

    def __proceed_with_pw_project(self, pw_project, project: Project) -> None:
        """Helper method to handle PW project data and copy it to given project"""

        project_properties = pw_project["properties"]
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
            project.favPersons.set(
                self.__get_fav_persons(project_properties["PROJECT_Muut_vastuuhenkilt"])
            )

        project.save()

    def __load_and_transform_phases(self):
        """Helper method to load phases from DB and transform to match PW format"""

        phase_map = {
            "proposal": "1. Hanke-ehdotus",
            "design": "1.5 Yleissuunnittelu",
            "programming": "2. Ohjelmointi",
            "draftInitiation": "3. Suunnittelun aloitus / Suunnitelmaluonnos",
            "draftApproval": "4. Katu- / puistosuunnitelmaehdotus ja hyväksyminen",
            "constructionPlan": "5. Rakennussuunnitelma",
            "constructionWait": "6. Odottaa rakentamista",
            "construction": "7. Rakentaminen",
            "warrantyPeriod": "8. Takuuaika",
            "completed": "9. Valmis / ylläpidossa",
        }
        return {phase_map[pph.value]: pph for pph in ProjectPhaseService.list_all()}

    def __load_and_transform_project_areas(self):
        """Helper method to load project areas from DB and transform to match PW format"""

        pa_map = {
            "honkasuo": "Honkasuo",
            "kalasatama": "Kalasatama",
            "kruunuvuorenranta": "Kruunuvuorenranta",
            "kuninkaantammi": "Kuninkaantammi",
            "lansisatama": "Länsisatama",
            "malminLentokenttaalue": "Malmin lentokenttäalue",
            "pasila": "Pasila",
            "ostersundom": "Östersundom",
        }

        return {pa_map[pa.value]: pa for pa in ProjectAreaService.list_all()}

    def __load_and_transform_responsible_zones(self):
        """Helper method to load responsible zones from DB and transform to match PW format"""

        rz_map = {
            "east": "Itä",
            "west": "Länsi",
            "north": "Pohjoinen",
        }

        return {rz_map[rz.value]: rz for rz in ResponsibleZoneService.list_all()}

    def __load_and_transform_project_types(self):
        """Helper method to load project types from DB and transform to match PW format"""

        pt_map = {
            "projectComplex": "hankekokonaisuus",
            "street": "katu",
            "cityRenewal": "kaupunkiuudistus",
            "traffic": "liikenne",
            "sports": "liikunta",
            "omaStadi": "OmaStadi-hanke",
            "projectArea": "projektialue",
            "park": "puisto",
            "bigTrafficProjects": "suuret liikennehankeet",
            "spesialtyStructures": "taitorakenne",
        }
        return {pt_map[pt.value]: pt for pt in ProjectTypeService.list_all()}

    def __load_and_transform_construction_phase_details(self):
        """Helper method to load construction phase details from DB and transform to match PW format"""

        pd_map = {
            "preConstruction": "1. Esirakentaminen",
            "firstPhase": "2. Ensimmäinen vaihe",
            "firstPhaseComplete": "3. Ensimmäinen vaihe valmis",
            "secondPhase": "4. Toinen vaihe / viimeistely",
        }

        return {
            pd_map[pd.value]: pd for pd in ConstructionPhaseDetailService.list_all()
        }

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
