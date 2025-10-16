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
from .utils.ProjectWiseDataMapper import to_pw_map

env = environ.Env()
env.escape_proxy = True

if path.exists(".env"):
    env.read_env(".env")

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"


class ProjectWiseService:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.auth = (env("PW_USERNAME"), env("PW_PASSWORD"))
        self.pw_api_url = env("PW_API_URL")
        self.pw_api_location_endpoint = env("PW_API_LOCATION_ENDPOINT")
        self.pw_api_project_metadata_endpoint = env("PW_API_PROJECT_META_ENDPOINT")
        self.pw_api_project_update_endpoint = env("PW_PROJECT_UPDATE_ENDPOINT")

        self.project_wise_data_mapper = ProjectWiseDataMapper()

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
            self.__sync_project_from_pw(project=project)

    def sync_project_from_pw(self, pw_id: str) -> None:
        """Method to synchronise project with given PW id with PW project data.\n"""

        logger.debug(f"Synchronizing given project with PW Id '{pw_id}' with PW")
        self.__sync_project_from_pw(ProjectService.get_by_hkr_id(hkr_id=pw_id))

    def __sync_project_from_pw(self, project: Project) -> None:
        """Method to synchronise given project from PW project data.\n
        Given project must have hkrId otherwise project will not be synchronized.
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
        except Exception as e:
            logger.error(
                "Error occurred while syncing project '{}' with PW id '{}'. \nError: {}".format(
                    project.id, project.hkrId, e
                )
            )

    def sync_project_to_pw(self, pw_id: str = None, data: dict = None, project: Project = None) -> None:
        """Method to synchronise project with given PW id to PW, or sync given project with data.\n"""

        if pw_id:
            # Legacy usage: sync by PW ID
            logger.debug(f"Synchronizing given project with PW Id '{pw_id}' to PW")
            project_obj = ProjectService.get_by_hkr_id(hkr_id=pw_id)
            self.__sync_project_to_pw(data={}, project=project_obj)
        elif project and data is not None:
            # New usage: sync with data and project object
            logger.debug(f"Synchronizing project '{project.name}' (ID: {project.id}) to PW")
            self.__sync_project_to_pw(data=data, project=project)
        else:
            logger.error("sync_project_to_pw called without proper parameters")

    def __sync_project_to_pw(self, data: dict, project: Project) -> None:
        """
        Sync project to ProjectWise using minimal payload approach.

        Sends ONLY fields that differ from PW current state (critical for success).
        Applies overwrite rules: protected fields preserved if PW has data.
        """
        if project.hkrId is None or str(project.hkrId).strip() == "":
            return
        try:
            current_pw_data = self.get_project_from_pw(project.hkrId)
            current_pw_properties = current_pw_data.get("relationshipInstances", [{}])[0].get("relatedInstance", {}).get("properties", {})

            filtered_data = self._apply_overwrite_rules(data, project, current_pw_properties)

            filtered_out = {k: v for k, v in data.items() if k not in filtered_data}
            if filtered_out:
                logger.debug(f"Fields filtered by overwrite rules: {list(filtered_out.keys())}")

            if not filtered_data:
                logger.info(f"No data to update for project '{project.name}' (HKR ID: {project.hkrId}) - all fields filtered by overwrite rules")
                logger.debug(f"Original data had {len(data)} fields: {list(data.keys())}")
                logger.debug(f"Current PW data: {current_pw_properties}")
                return

            pw_project_data = self.project_wise_data_mapper.convert_to_pw_data(
                data=filtered_data
            )

            if pw_project_data:
                pw_instance_id = current_pw_data["relationshipInstances"][0]["relatedInstance"]["instanceId"]

                (
                    schema_name,
                    class_name,
                    *others,
                ) = self.pw_api_project_update_endpoint.split("/")

                # IO-396: PW only accepts updates with minimal payloads (changed fields only)
                pw_project_data_minimal = {}
                for field_name, field_value in pw_project_data.items():
                    pw_current_value = current_pw_properties.get(field_name, '')

                    infra_empty = not field_value or (isinstance(field_value, str) and not field_value.strip())
                    pw_empty = not pw_current_value or (isinstance(pw_current_value, str) and not pw_current_value.strip())

                    # Include if values differ (updates, additions, or deletions)
                    if (not infra_empty and not pw_empty and field_value != pw_current_value) or \
                       (not infra_empty and pw_empty) or \
                       (infra_empty and not pw_empty):
                        pw_project_data_minimal[field_name] = field_value

                logger.info(f"=" * 80)
                logger.info(f"UPDATING PROJECT: '{project.name}' (HKR ID: {project.hkrId})")
                logger.info(f"PW Instance ID: {pw_instance_id}")
                logger.info(f"Fields to update: {len(pw_project_data_minimal)} of {len(pw_project_data)} total")

                if not pw_project_data_minimal:
                    logger.info("No fields to update - all values match PW")
                    logger.info("=" * 80)
                    return

                sample_fields = list(pw_project_data_minimal.items())[:5]
                logger.info(f"Sample fields: {dict(sample_fields)}")
                if len(pw_project_data_minimal) > 5:
                    logger.info(f"  ... and {len(pw_project_data_minimal) - 5} more fields")
                logger.debug(f"All fields: {list(pw_project_data_minimal.keys())}")

                pw_update_data = {
                    "instance": {
                        "schemaName": schema_name,
                        "className": class_name,
                        "instanceId": pw_instance_id,
                        "changeState": "modified",
                        "properties": pw_project_data_minimal,
                    }
                }

                api_url = f"{self.pw_api_url}{self.pw_api_project_update_endpoint}{pw_instance_id}"

                logger.debug(f"PW update endpoint: {api_url}")
                logger.debug(f"Complete update request data: {pw_update_data}")

                try:
                    response = self.session.post(url=api_url, json=pw_update_data)
                    response.raise_for_status()

                    logger.info(f"SUCCESS: Updated {len(pw_project_data_minimal)} fields in PW")
                    logger.info(f"=" * 80)
                    return

                except requests.exceptions.RequestException as request_error:
                    logger.error(f"=" * 80)
                    logger.error(f"PW UPDATE FAILED: '{project.name}' (HKR ID: {project.hkrId})")
                    logger.error(f"Error type: {type(request_error).__name__}")
                    logger.error(f"Error details: {str(request_error)}")
                    logger.error(f"Request URL: {api_url}")
                    logger.error(f"Fields attempted: {list(pw_project_data_minimal.keys())}")

                    if hasattr(request_error, 'response') and request_error.response is not None:
                        logger.error(f"Status Code: {request_error.response.status_code}")
                        try:
                            error_detail = request_error.response.json()
                            logger.error(f"PW Error Response: {error_detail}")
                        except Exception:
                            logger.error(f"PW Error Response: {request_error.response.text[:500]}")
                        logger.error(f"Full payload sent: {pw_project_data_minimal}")

                        if current_pw_properties:
                            critical_pw_fields = {k: v for k, v in current_pw_properties.items()
                                                 if any(field in k for field in ['vaihe', 'Toimiala', 'luokka', 'piirin', 'Ohjelmoitu'])}
                            logger.error(f"PW current state: {critical_pw_fields}")

                    logger.error(f"=" * 80)
                    raise PWProjectResponseError(f"PW update failed for project '{project.name}' (HKR ID: {project.hkrId}): {str(request_error)}")

                except Exception as unexpected_error:
                    logger.error(f"=" * 80)
                    logger.error(f"UNEXPECTED ERROR during PW update: '{project.name}' (HKR ID: {project.hkrId})")
                    logger.error(f"Error type: {type(unexpected_error).__name__}")
                    logger.error(f"Error details: {str(unexpected_error)}")
                    logger.error(f"Request URL: {api_url}")
                    logger.error(f"Fields attempted: {list(pw_project_data_minimal.keys())}")
                    logger.error(f"=" * 80)
                    raise PWProjectResponseError(f"Unexpected error updating project '{project.name}' (HKR ID: {project.hkrId}): {str(unexpected_error)}")
            else:
                logger.info(f"No PW data generated for project '{project.name}' (HKR ID: {project.hkrId})")
        except (
            ProjectWiseDataFieldNotFound,
            PWProjectResponseError,
            PWProjectNotFoundError,
        ) as e:
            logger.error(
                f"Error occured while syncing project '{project.id}' to PW with data '{data}'. {e}"
            )
            # Re-raise the exception so mass update can count it as an error
            raise

    def _apply_overwrite_rules(self, data: dict, project: Project, current_pw_properties: dict) -> dict:
        """
        Apply overwrite rules: send data when we have it, preserve PW data when we don't.
        Protected fields never overwritten if PW has data.
        """
        filtered_data = {}

        for field_name, field_value in data.items():
            try:
                should_include_field = self._should_include_field_in_update(
                    field_name, field_value, current_pw_properties
                )

                if should_include_field:
                    filtered_data[field_name] = field_value

            except Exception as e:
                logger.error(f"Error processing field '{field_name}': {str(e)}")
                logger.warning(f"SKIP: Field '{field_name}' - validation failed")

        return filtered_data

    def _should_include_field_in_update(self, field_name: str, field_value, current_pw_properties: dict) -> bool:
        """
        Check if field should be included based on overwrite rules.
        Protected fields preserved if PW has data, regular fields sent when infra tool has data.
        """
        protected_fields = {
            'description', 'presenceStart', 'presenceEnd',
            'visibilityStart', 'visibilityEnd', 'masterPlanAreaNumber',
            'trafficPlanNumber', 'bridgeNumber'
        }

        pw_field_name = self._get_pw_field_mapping().get(field_name)
        if not pw_field_name:
            logger.debug(f"Field '{field_name}' has no PW mapping - including anyway")
            return True

        pw_value = current_pw_properties.get(pw_field_name, '')
        project_empty = not field_value or (isinstance(field_value, str) and not field_value.strip())
        pw_has_data = pw_value and (not isinstance(pw_value, str) or pw_value.strip())

        if field_name in protected_fields:
            if pw_has_data:
                logger.debug(f"SKIP: Protected field '{field_name}' - PW has data")
                return False
            logger.debug(f"INCLUDE: Protected field '{field_name}' - PW empty")
            return True

        if project_empty and pw_has_data:
            logger.debug(f"SKIP: Field '{field_name}' - infra empty, PW has data")
            return False

        logger.debug(f"INCLUDE: Field '{field_name}'")
        return True

    def _get_pw_field_mapping(self) -> dict:
        """Get mapping from internal field names to PW field names."""
        field_mapping = {}

        for field_name, mapping in to_pw_map.items():
            if isinstance(mapping, str):
                field_mapping[field_name] = mapping
            elif isinstance(mapping, dict) and 'field' in mapping:
                field_mapping[field_name] = mapping['field']
            elif isinstance(mapping, dict) and 'values' in mapping:
                if isinstance(mapping['values'], list) and mapping['values']:
                    field_mapping[field_name] = mapping['values'][0]

        return field_mapping

    def _filter_projects_for_test_scope(self, projects):
        """
        Filter projects for the test scope: 8 04 Puistot ja liikunta-alueet Puistojen peruskorjaus Keskinen suurpiiri
        Uses environment variable PW_TEST_SCOPE_CLASS_ID for flexibility between environments.
        """
        # Get test scope class ID from environment variable
        test_scope_subclass_id = env("PW_TEST_SCOPE_CLASS_ID", default=None)

        if not test_scope_subclass_id:
            logger.warning("PW_TEST_SCOPE_CLASS_ID environment variable not set - returning empty queryset")
            return projects.none()

        try:
            filtered_projects = projects.filter(projectClass__id=test_scope_subclass_id)
            logger.info(f"Filtered projects for test scope: {filtered_projects.count()} projects found under subClass {test_scope_subclass_id}")
            return filtered_projects
        except Exception as e:
            logger.error(f"Error filtering projects for test scope: {str(e)}")
            logger.error(f"Make sure PW_TEST_SCOPE_CLASS_ID environment variable is set to a valid ProjectClass UUID")
            logger.warning("Returning empty queryset due to filtering error")
            return projects.none()

    def sync_all_projects_to_pw(self):
        """Mass update all programmed projects with HKR IDs to ProjectWise."""
        return self._mass_update_projects_to_pw(use_test_scope=False)

    def sync_all_projects_to_pw_with_test_scope(self):
        """Mass update test scope projects only (filtered by class hierarchy)."""
        return self._mass_update_projects_to_pw(use_test_scope=True)

    def _mass_update_projects_to_pw(self, use_test_scope: bool = False):
        """Core mass update implementation. Returns list of update logs."""
        all_projects = Project.objects.filter(programmed=True, hkrId__isnull=False)

        if use_test_scope:
            projects = self._filter_projects_for_test_scope(all_projects)
            scope_description = "test scope"
        else:
            projects = all_projects
            scope_description = "all programmed projects"

        total_projects = projects.count()
        logger.info(f"Starting mass update of {total_projects} {scope_description} to PW")

        if total_projects == 0:
            logger.warning(f"No projects found for mass update ({scope_description})")
            return []

        update_log = []
        successful_updates = 0
        skipped_updates = 0
        errors = 0

        for i, project in enumerate(projects, 1):
            logger.info(f"\n{'='*100}")
            logger.info(f"PROCESSING PROJECT {i}/{total_projects}: {project.name} (HKR ID: {project.hkrId})")
            logger.info(f"{'='*100}")

            try:
                # Create comprehensive project data for mass update
                project_data = self._create_project_data_for_mass_update(project)
                logger.debug(f"Created project data with {len(project_data)} fields: {list(project_data.keys())}")

                if not project_data:
                    logger.info(f"No data to sync for project '{project.name}' - all fields are None")
                    update_log.append({
                        'project_id': str(project.id),
                        'project_name': project.name,
                        'hkr_id': project.hkrId,
                        'status': 'skipped',
                        'reason': 'no_data'
                    })
                    skipped_updates += 1
                    continue

                # Use the existing sync method which has overwrite rules
                self.__sync_project_to_pw(data=project_data, project=project)

                update_log.append({
                    'project_id': str(project.id),
                    'project_name': project.name,
                    'hkr_id': project.hkrId,
                    'updated_fields': list(project_data.keys()),
                    'status': 'success'
                })
                successful_updates += 1

            except Exception as e:
                logger.error(f"Failed to update project {project.name}: {str(e)}")
                update_log.append({
                    'project_id': str(project.id),
                    'project_name': project.name,
                    'hkr_id': project.hkrId,
                    'status': 'error',
                    'error': str(e)
                })
                errors += 1

        # Log comprehensive summary
        logger.info(f"Mass update completed ({scope_description}): {successful_updates} successful, {skipped_updates} skipped, {errors} errors")

        if errors > 0:
            logger.warning(f"{errors} projects failed to update - check logs for details")

        return update_log

    def _create_project_data_for_mass_update(self, project: Project) -> dict:
        """Build and validate project data dict for PW sync. Excludes None values."""
        if not isinstance(project, Project):
            raise TypeError("project must be a Project instance")

        if not project.id:
            raise ValueError("project must have an ID")
        if not project.programmed:
            raise ValueError("project must be programmed")
        if not project.hkrId:
            raise ValueError("project must have an hkrId")
        if not project.name:
            raise ValueError("project must have a name")

        if project.hkrId:
            project.hkrId = str(project.hkrId)
        if project.name and not isinstance(project.name, str):
            raise TypeError("name must be a string")
        if project.description and not isinstance(project.description, str):
            raise TypeError("description must be a string")

        raw_project_data = {
            'name': project.name,
            'description': project.description,
            'address': project.address,
            'entityName': project.entityName,
            'phase': str(project.phase.id) if project.phase else None,
            'type': str(project.type.id) if project.type else None,
            'projectClass': str(project.projectClass.id) if project.projectClass else None,
            'projectDistrict': str(project.projectDistrict.id) if project.projectDistrict else None,
            'area': str(project.area.id) if project.area else None,
            'responsibleZone': str(project.responsibleZone.id) if project.responsibleZone else None,
            'constructionPhaseDetail': str(project.constructionPhaseDetail.id) if project.constructionPhaseDetail else None,
            'programmed': project.programmed,
            'estPlanningStart': project.estPlanningStart,
            'estPlanningEnd': project.estPlanningEnd,
            'estConstructionStart': project.estConstructionStart,
            'estConstructionEnd': project.estConstructionEnd,
            'presenceStart': project.presenceStart,
            'presenceEnd': project.presenceEnd,
            'visibilityStart': project.visibilityStart,
            'visibilityEnd': project.visibilityEnd,
            'planningStartYear': project.planningStartYear,
            'constructionEndYear': project.constructionEndYear,
            'gravel': project.gravel,
            'louhi': project.louhi,
            'masterPlanAreaNumber': project.masterPlanAreaNumber,
            'trafficPlanNumber': project.trafficPlanNumber,
            'bridgeNumber': project.bridgeNumber,
            'personPlanning': str(project.personPlanning.id) if project.personPlanning else None,
            'personConstruction': str(project.personConstruction.id) if project.personConstruction else None,
        }

        cleaned_data = {k: v for k, v in raw_project_data.items() if v is not None}
        logger.debug(f"Built project data for {project.name} with {len(cleaned_data)} fields")
        return cleaned_data

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
        if description != "Kuvaus puuttuu" and description != "":
            project.description = description

        if project_properties["PROJECT_Kadun_tai_puiston_nimi"]:
            project.address = project_properties["PROJECT_Kadun_tai_puiston_nimi"]

        if project_properties["PROJECT_Hankkeen_vaihe"]:
            project.phase = (
                self.project_phases[project_properties["PROJECT_Hankkeen_vaihe"]]
                if project_properties["PROJECT_Hankkeen_vaihe"] in self.project_phases
                else self.project_phases["2. Ohjelmointi"]
            )

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
                logger.debug(
                    "Person planning: {} for project {}".format(
                        planning_person_data,
                        project.hkrId,
                    )
                )
                project.personPlanning = planning_person

        if project_properties["PROJECT_Vastuuhenkil_rakennuttaminen"]:
            construction_person = self.__get_project_person(
                person_data=project_properties["PROJECT_Vastuuhenkil_rakennuttaminen"]
            )

            if construction_person:
                logger.debug(
                    "Person construction: {} for project {}".format(
                        project_properties["PROJECT_Vastuuhenkil_rakennuttaminen"],
                        project.hkrId,
                    )
                )
                project.personConstruction = construction_person

        if project_properties["PROJECT_Muut_vastuuhenkilt"]:
            logger.debug(
                "Person others: {} for project {}".format(
                    project_properties["PROJECT_Muut_vastuuhenkilt"],
                    project.hkrId,
                )
            )
            project.otherPersons = project_properties["PROJECT_Muut_vastuuhenkilt"]

        project.save()

    def __get_project_person(self, person_data: str) -> Person:
        """Helper method to load person from DB with PW data"""

        person_data = person_data.strip().replace(", ", ",")
        logger.debug("person_data: {}".format(person_data))
        if not person_data.rstrip(","):
            logger.debug("No person data present")
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


class PWProjectNotFoundError(RuntimeError):
    """Error representing not found project in PW error"""

    pass


class PWProjectResponseError(RuntimeError):
    """Error representing PW error with non status code of 200"""

    pass
