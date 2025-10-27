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

from .utils import (
    ProjectWiseDataMapper,
    ProjectWiseDataFieldNotFound,
    create_comprehensive_project_data,
)
from .utils.PWConfig import PWConfig
from .utils.ProjectWiseDataMapper import to_pw_map

env = environ.Env()
env.escape_proxy = True

if path.exists(".env"):
    env.read_env(".env")

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "ALL:@SECLEVEL=1"


class ProjectWiseService:
    """Service for ProjectWise integration."""

    # Class constants - defined once, used everywhere
    HIERARCHICAL_FIELD_ORDER = [
        'PROJECT_Pluokka',           # Main classification
        'PROJECT_Luokka',            # Sub-classification
        'PROJECT_Alaluokka',         # Sub-sub-classification
        'PROJECT_Suurpiirin_nimi',   # District
        'PROJECT_Kaupunginosan_nimi',# Sub-district
        'PROJECT_Osa_alue'           # Sub-area
    ]
    HIERARCHICAL_FIELDS = set(HIERARCHICAL_FIELD_ORDER)  # O(1) lookup

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.auth = (env("PW_USERNAME"), env("PW_PASSWORD"))
        self.pw_api_url = env("PW_API_URL")
        self.pw_api_location_endpoint = env("PW_API_LOCATION_ENDPOINT")
        self.pw_api_project_metadata_endpoint = env("PW_API_PROJECT_META_ENDPOINT")
        self.pw_api_project_update_endpoint = env("PW_PROJECT_UPDATE_ENDPOINT")
        
        self.pw_sync_enabled = env.bool("PW_SYNC_ENABLED", default=False)
        
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

    @staticmethod
    def _normalize_classification_format(value):
        """
        Normalize classification format for comparison.
        '8 04 Puistot' and '804 Puistot' are treated as equivalent.
        Returns normalized format (without space: '804 Puistot').
        """
        if not isinstance(value, str):
            return value
        # Pattern: "X YY Rest" → "XYY Rest"
        match = re.match(r'^(\d) (\d{2}) (.+)$', value)
        if match:
            return match.group(1) + match.group(2) + ' ' + match.group(3)
        return value

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

    def _update_hierarchical_fields_one_by_one(self, instance_id, hierarchical_fields, project_name, hkr_id):
        """
        Update classification/location fields one at a time.
        PW governance rules require individual updates for these fields.

        Args:
            instance_id: PW instance ID
            hierarchical_fields: Dict of field_name: value for hierarchical fields
            project_name: Project name for logging
            hkr_id: HKR ID for logging

        Returns:
            Tuple of (success_count, total_count)
        """
        # Use class constant instead of local definition

        success_count = 0
        total_count = len(hierarchical_fields)

        logger.info(f"Updating {total_count} hierarchical fields one-at-a-time for '{project_name}' (HKR {hkr_id})")

        for field_name in self.HIERARCHICAL_FIELD_ORDER:
            if field_name not in hierarchical_fields:
                continue

            field_value = hierarchical_fields[field_name]

            schema_name, class_name, *_ = self.pw_api_project_update_endpoint.split("/")

            pw_update_data = {
                "instance": {
                    "schemaName": schema_name,
                    "className": class_name,
                    "instanceId": instance_id,
                    "changeState": "modified",
                    "properties": {field_name: field_value}
                }
            }

            api_url = f"{self.pw_api_url}{self.pw_api_project_update_endpoint}{instance_id}"

            try:
                response = self.session.post(url=api_url, json=pw_update_data)

                if response.status_code == 200:
                    logger.info(f"  [OK] {field_name}: '{field_value}' - SUCCESS")
                    success_count += 1
                else:
                    logger.warning(f"  [FAIL] {field_name}: '{field_value}' - FAILED (status {response.status_code})")
                    try:
                        error_detail = response.json()
                        logger.warning(f"    Error: {error_detail.get('errorMessage', 'Unknown')}")
                    except:
                        pass

                # Small delay between updates
                time.sleep(PWConfig.HIERARCHICAL_FIELD_DELAY)

            except Exception as e:
                logger.error(f"  [ERROR] {field_name}: Exception - {str(e)}")

        return success_count, total_count

    def sync_project_to_pw(self, pw_id: str = None, data: dict = None, project: Project = None) -> None:
        """Method to synchronise project with given PW id to PW, or sync given project with data.\n"""
        
        if not self.pw_sync_enabled:
            logger.warning(
                "ProjectWise sync is DISABLED (PW_SYNC_ENABLED=False). "
                "Skipping sync to prevent dev/local data from reaching production PW. "
                "Set PW_SYNC_ENABLED=True in production environment only."
            )
            return

        if pw_id:
            logger.debug(f"Synchronizing given project with PW Id '{pw_id}' to PW")
            project_obj = ProjectService.get_by_hkr_id(hkr_id=pw_id)
            self.__sync_project_to_pw(data={}, project=project_obj)
        elif project and data is not None:
            logger.debug(f"Synchronizing project '{project.name}' (ID: {project.id}) to PW")
            self.__sync_project_to_pw(data=data, project=project)
        else:
            logger.error("sync_project_to_pw called without proper parameters")

    def __sync_project_to_pw(self, data: dict, project: Project) -> None:
        """Method to synchronise given project to PW
        Given project must have hkrId otherwise project will not be synchronized.
        Implements overwrite rules: only update if infra tool field is empty, except for protected fields.
        """
        if project.hkrId is None or str(project.hkrId).strip() == "":
            return
        try:
            # Get current PW data to apply overwrite rules
            current_pw_data = self.get_project_from_pw(project.hkrId)
            current_pw_properties = current_pw_data.get("relationshipInstances", [{}])[0].get("relatedInstance", {}).get("properties", {})

            # Apply overwrite rules to filter data before sending to PW
            filtered_data = self._apply_overwrite_rules(data, project, current_pw_properties)

            # Log filtered fields for diagnostics
            filtered_out = {k: v for k, v in data.items() if k not in filtered_data}
            if filtered_out:
                logger.debug(f"Fields filtered out by overwrite rules for '{project.name}': {list(filtered_out.keys())}")
                
                field_categories = {
                    'classification': [f for f in filtered_out.keys() if f in PWConfig.CLASSIFICATION_FIELDS],
                    'protected': [f for f in filtered_out.keys() if f in PWConfig.PROTECTED_FIELDS],
                    'empty_tool': [f for f in filtered_out.keys() if f not in PWConfig.CLASSIFICATION_FIELDS and f not in PWConfig.PROTECTED_FIELDS]
                }
                
                for category, fields in field_categories.items():
                    if fields:
                        logger.info(f"  Filtered ({category}): {fields}")

            if not filtered_data:
                logger.info(f"No data to update for project '{project.name}' (HKR ID: {project.hkrId}) - all fields filtered by overwrite rules")
                logger.debug(f"Original data had {len(data)} fields: {list(data.keys())}")
                logger.debug(f"Current PW data: {current_pw_properties}")
                return

            pw_project_data = self.project_wise_data_mapper.convert_to_pw_data(
                data=filtered_data, project=project
            )

            # Log data being sent to PW
            logger.info(f"Sending {len(pw_project_data)} fields to PW for '{project.name}': {list(pw_project_data.keys())}")
            logger.debug(f"Full PW data payload: {pw_project_data}")

            if pw_project_data:
                pw_instance_id = current_pw_data["relationshipInstances"][0]["relatedInstance"]["instanceId"]

                schema_name, class_name, *_ = self.pw_api_project_update_endpoint.split("/")
                api_url = f"{self.pw_api_url}{self.pw_api_project_update_endpoint}{pw_instance_id}"

                logger.info(f"=" * 80)
                logger.info(f"UPDATING PROJECT: '{project.name}' (HKR ID: {project.hkrId})")
                logger.info(f"PW Instance ID: {pw_instance_id}")

                # Split hierarchical fields from normal fields
                # Hierarchical fields need one-at-a-time updates due to PW governance rules
                # Use class constant instead of local definition

                hierarchical_to_update = {k: v for k, v in pw_project_data.items() if k in self.HIERARCHICAL_FIELDS}
                normal_to_update = {k: v for k, v in pw_project_data.items() if k not in self.HIERARCHICAL_FIELDS}

                normal_success = False
                hierarchical_success_count = 0
                hierarchical_total_count = len(hierarchical_to_update)

                # Update normal fields in batch (existing behavior)
                if normal_to_update:
                    logger.info(f"Updating {len(normal_to_update)} normal fields in batch")
                    logger.debug(f"Normal fields: {list(normal_to_update.keys())}")

                    pw_update_data = {
                        "instance": {
                            "schemaName": schema_name,
                            "className": class_name,
                            "instanceId": pw_instance_id,
                            "changeState": "modified",
                            "properties": normal_to_update,
                        }
                    }

                    try:
                        response = self.session.post(url=api_url, json=pw_update_data)

                        if response.status_code == 200:
                            logger.info("[OK] Normal fields updated successfully")
                            normal_success = True
                        else:
                            logger.error(f"[FAIL] Normal fields update failed (status {response.status_code})")
                            try:
                                error_detail = response.json()
                                logger.error(f"  Error: {error_detail}")
                            except:
                                logger.error(f"  Error: {response.reason}")

                            # Raise exception if normal fields fail - this is unexpected
                            raise PWProjectResponseError(
                                f"Normal field update failed for '{project.name}' (HKR {project.hkrId}): "
                                f"Status {response.status_code}"
                            )

                    except requests.exceptions.RequestException as e:
                        logger.error(f"[ERROR] Normal fields update - network error: {str(e)}")
                        raise PWProjectResponseError(f"Network error updating '{project.name}': {str(e)}")
                else:
                    logger.info("No normal fields to update")
                    normal_success = True  # No normal fields means nothing to fail

                # Update hierarchical fields one-at-a-time (new behavior)
                if hierarchical_to_update:
                    hierarchical_success_count, hierarchical_total_count = self._update_hierarchical_fields_one_by_one(
                        pw_instance_id,
                        hierarchical_to_update,
                        project.name,
                        project.hkrId
                    )

                    if hierarchical_success_count == hierarchical_total_count:
                        logger.info(f"[OK] All {hierarchical_total_count} hierarchical fields updated successfully")
                    elif hierarchical_success_count > 0:
                        logger.warning(
                            f"[PARTIAL] {hierarchical_success_count}/{hierarchical_total_count} "
                            f"hierarchical fields updated"
                        )
                    else:
                        logger.error(f"[FAIL] All {hierarchical_total_count} hierarchical field updates failed")
                else:
                    logger.info("No hierarchical fields to update")

                # Overall result
                total_attempted = len(normal_to_update) + hierarchical_total_count
                total_succeeded = (len(normal_to_update) if normal_success else 0) + hierarchical_success_count

                logger.info(f"=" * 80)
                logger.info(
                    f"UPDATE RESULT: {total_succeeded}/{total_attempted} fields updated for "
                    f"'{project.name}' (HKR {project.hkrId})"
                )
                logger.info(f"=" * 80)

                # Don't raise exception if at least some fields updated successfully
                # This allows partial updates (e.g., normal fields succeed even if hierarchical fail)
                if total_succeeded == 0 and total_attempted > 0:
                    raise PWProjectResponseError(
                        f"All field updates failed for '{project.name}' (HKR {project.hkrId})"
                    )
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
        Apply overwrite rules to filter data before sending to PW.

        Rules:
        - Send infra tool data when it has a value (overwrites PW data)
        - Skip fields when infra tool is empty BUT PW has data (preserves existing PW data)
        - EXCEPTION: Never overwrite protected fields if they have data in PW (always preserve)
        """
        filtered_data = {}

        for field_name, field_value in data.items():
            try:
                should_include_field = self._should_include_field_in_update(
                    field_name, field_value, project, current_pw_properties
                )

                if should_include_field:
                    filtered_data[field_name] = field_value

            except Exception as e:
                logger.error(f"Error processing field '{field_name}': {str(e)}")
                logger.warning(f"SKIP: Field '{field_name}' - validation failed, not sending to PW")
                # BUG FIX: SKIP fields that fail validation instead of including them
                # Previously we included failed fields "to be safe", but this caused us to send
                # locked/invalid fields to PW, which PW would silently reject
                # Do NOT add to filtered_data - skip this field

        return filtered_data

    def _should_include_field_in_update(self, field_name: str, field_value, project: Project, current_pw_properties: dict) -> bool:
        """
        Determine if a specific field should be included in the PW update based on overwrite rules.
        """
        # Protected fields: never overwrite if PW has data (IO-396 requirements)
        protected_fields = PWConfig.PROTECTED_FIELDS

        # Get PW field mapping
        pw_field_name = self._get_pw_field_mapping().get(field_name)
        if not pw_field_name:
            # No mapping found, include the field (might be handled by other logic)
            logger.debug(f"Field '{field_name}' has no PW mapping - including anyway")
            return True

        # Get current values
        # BUG FIX: Use field_value from data dict (UUID strings) instead of getattr (objects)
        # The field_value parameter contains properly formatted UUID strings for related objects,
        # while getattr would return the actual ProjectPhase/ProjectType objects
        pw_value = current_pw_properties.get(pw_field_name, '')

        # Check if values are empty
        project_empty = not field_value or (isinstance(field_value, str) and not field_value.strip())
        pw_has_data = pw_value and (not isinstance(pw_value, str) or pw_value.strip())

        # Verbose logging for critical fields
        if field_name in ['programmed', 'phase', 'type', 'projectClass', 'projectDistrict']:
            project_obj_value = getattr(project, field_name, None)
            logger.info(f"CRITICAL FIELD '{field_name}': data_value={field_value}, project_obj={project_obj_value}, pw_value={pw_value}, tool_empty={project_empty}, pw_has_data={pw_has_data}")

        # Classification hierarchy fields (projectClass, projectDistrict): attempt to send
        # If PW rejects (e.g., folder structure doesn't exist), the try-catch mechanism will handle it
        # Previously these were preemptively blocked, but we should let PW decide what it accepts

        # For type, phase, programmed: we attempt to send and use try-catch retry logic
        # This allows PW to decide what it accepts/rejects with graceful fallback

        # Apply overwrite rules for regular fields
        if field_name in protected_fields:
            # Protected field: never overwrite if PW has data
            if pw_has_data:
                logger.debug(f"SKIP: Protected field '{field_name}' - PW has data: '{pw_value}'")
                return False
            else:
                logger.debug(f"INCLUDE: Protected field '{field_name}' - PW has no data")
                return True
        else:
            # Regular field: only skip if infra tool is empty but PW has data
            if project_empty and pw_has_data:
                logger.debug(f"SKIP: Field '{field_name}' - infra tool empty but PW has data: '{pw_value}'")
                return False
            else:
                if not project_empty:
                    logger.debug(f"INCLUDE: Field '{field_name}' - infra tool has data (value: {field_value})")
                else:
                    logger.debug(f"INCLUDE: Field '{field_name}' - both infra tool and PW are empty")
                return True

    def _get_pw_field_mapping(self) -> dict:
        """
        Get the mapping from project fields to PW field names.
        Uses ProjectWiseDataMapper.to_pw_map for complete and accurate mappings.
        """

        # Build simplified mapping for _should_include_field_in_update logic
        # Extract the actual PW field names from the complex mapping structure
        field_mapping = {}

        for field_name, mapping in to_pw_map.items():
            if isinstance(mapping, str):
                # Simple string mapping
                field_mapping[field_name] = mapping
            elif isinstance(mapping, dict) and 'field' in mapping:
                # Complex mapping with 'field' key
                field_mapping[field_name] = mapping['field']
            elif isinstance(mapping, dict) and 'values' in mapping:
                # Enum mapping - use first field name from values list
                if isinstance(mapping['values'], list) and mapping['values']:
                    field_mapping[field_name] = mapping['values'][0]

        return field_mapping


    def sync_all_projects_to_pw(self):
        """
        PRODUCTION-READY mass update of all programmed projects to ProjectWise.
        Implements overwrite rules and comprehensive logging.
        Only processes programmed projects with HKR IDs.
        """
        return self._mass_update_projects_to_pw()

    def _mass_update_projects_to_pw(self):
        """
        Core mass update implementation with overwrite rules and comprehensive logging.
        Processes all programmed projects with HKR IDs.

        Returns:
            List of update logs with detailed results for each project
        """
        if not self.pw_sync_enabled:
            logger.error(
                "=" * 100 + "\n"
                "MASS UPDATE BLOCKED: ProjectWise sync is DISABLED\n"
                "PW_SYNC_ENABLED=False prevents dev/local environments from syncing to production PW.\n"
                "This is a safety feature. Set PW_SYNC_ENABLED=True in production .env only.\n" +
                "=" * 100
            )
            return []
        
        projects = Project.objects.filter(programmed=True, hkrId__isnull=False)
        total_projects = projects.count()
        logger.info(f"Starting mass update of {total_projects} all programmed projects to PW")

        if total_projects == 0:
            logger.warning(f"No projects found for mass update (all programmed projects)")
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
        logger.info(f"Mass update completed (all programmed projects): {successful_updates} successful, {skipped_updates} skipped, {errors} errors")

        if errors > 0:
            logger.warning(f"{errors} projects failed to update - check logs for details")

        return update_log

    def _create_project_data_for_mass_update(self, project: Project) -> dict:
        """
        Create project data dictionary for mass updates.
        
        Validates project before delegating to shared data builder.

        Args:
            project: The project object to extract data from

        Returns:
            Dictionary with project fields, excluding None values

        Raises:
            ValueError: If project is invalid or missing required attributes
            TypeError: If project is not a Project instance
        """
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

        data = create_comprehensive_project_data(project)

        if 'programmed' in data:
            logger.debug(f"Project '{project.name}' programmed status: {project.programmed} (will convert to {'Kyllä' if project.programmed else 'Ei'})")

        logger.debug(f"Built project data for {project.name} with {len(data)} fields")
        return data

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
