import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from infraohjelmointi_api.services import ProjectDistrictService
from ...models import Project
from ..ProjectAreaService import ProjectAreaService
from ..ProjectPhaseService import ProjectPhaseService
from ..ResponsibleZoneService import ResponsibleZoneService
from ..ProjectTypeService import ProjectTypeService
from ..ConstructionPhaseDetailService import ConstructionPhaseDetailService
from ..ProjectClassService import ProjectClassService
from ..PersonService import PersonService

from infraohjelmointi_api.services.utils.FieldMappingConfig import FieldMappingConfig
from infraohjelmointi_api.services.utils.FieldMappingDictionaries import FIELD_MAPPER_LOOKUP

logger = logging.getLogger("infraohjelmointi_api")


class ProjectWiseDataMapper:
    """ProjectWise data mapper."""

    def __init__(self):
        self.field_config = FieldMappingConfig()

    def convert_to_pw_data(self, data: dict, project: Project) -> dict:
        """
        Convert project data to ProjectWise format with proper error handling.

        Args:
            data: Dictionary of project data (internal field names)
            project: Project object for additional context

        Returns:
            Dictionary with ProjectWise field names and values
        """
        pw_data = {}

        for field_name, value in data.items():
            try:
                mapped_data = self._map_field(field_name, value, project)
                if mapped_data:
                    pw_data.update(mapped_data)
            except Exception as e:
                logger.warning(f"Failed to map field '{field_name}': {e}")
                continue

        return pw_data

    def _map_field(self, field_name: str, value: Any, project: Project) -> Dict[str, Any]:
        """
        Map a single field with proper type handling.

        Args:
            field_name: Name of the field to map
            value: Value to map
            project: Project object for context

        Returns:
            Dictionary with PW field name(s) and value(s)
        """
        if not self.field_config.is_supported_field(field_name):
            logger.debug(f"Field '{field_name}' not supported")
            return {}

        field_type = self.field_config.get_field_type(field_name)

        if field_type == "basic":
            return self._map_basic_field(field_name, value)
        elif field_type == "boolean":
            return self._map_boolean_field(field_name, value)
        elif field_type == "integer":
            return self._map_integer_field(field_name, value)
        elif field_type == "date":
            return self._map_date_field(field_name, value)
        elif field_type == "listvalue":
            return self._map_listvalue_field(field_name, value, project)
        elif field_type == "enum":
            return self._map_enum_field(field_name, value, project)
        else:
            logger.warning(f"Unsupported field type '{field_type}' for field '{field_name}'")
            return {}

    def _map_basic_field(self, field_name: str, value: Any) -> Dict[str, Any]:
        """Map basic string fields."""
        pw_field = self.field_config.get_pw_field_name(field_name)
        return {pw_field: value} if value is not None else {}

    def _map_boolean_field(self, field_name: str, value: Any) -> Dict[str, Any]:
        """Map boolean fields to PW text values."""
        config = self.field_config.BOOLEAN_FIELDS[field_name]
        pw_value = config.true_value if str(value).lower() == "true" else config.false_value
        return {config.field: pw_value}

    def _map_integer_field(self, field_name: str, value: Any) -> Dict[str, Any]:
        """Map integer fields."""
        pw_field = self.field_config.get_pw_field_name(field_name)
        return {pw_field: int(value)} if value is not None else {}

    def _map_date_field(self, field_name: str, value: Any) -> Dict[str, Any]:
        """Map date fields with proper formatting."""
        config = self.field_config.DATE_FIELDS[field_name]

        if not value:
            return {config.field: ""}

        try:
            if isinstance(value, str):
                formatted_date = datetime.strptime(value, config.from_format).strftime(config.to_format)
            elif isinstance(value, datetime):
                formatted_date = value.strftime(config.to_format)
            elif hasattr(value, 'year'):  # Handle datetime.date objects
                dt = datetime.combine(value, datetime.min.time())
                formatted_date = dt.strftime(config.to_format)
            else:
                formatted_date = ""

            return {config.field: formatted_date}
        except Exception as e:
            logger.warning(f"Failed to format date field '{field_name}': {e}")
            return {config.field: ""}

    def _map_listvalue_field(self, field_name: str, value: Any, project: Project) -> Dict[str, Any]:
        """Map list value fields using service lookups."""
        config = self.field_config.LIST_VALUE_FIELDS[field_name]

        if not value:
            return {config.field: None}

        # Get the field mapper
        field_mapper = FIELD_MAPPER_LOOKUP[config.mapper]

        # Get the actual value from the service
        service_value = self._get_service_value(field_name, value)
        if not service_value:
            return {config.field: None}

        # Map to PW value
        pw_value = field_mapper.get(service_value)
        return {config.field: pw_value} if pw_value else {config.field: None}

    def _map_enum_field(self, field_name: str, value: Any, project: Project) -> Dict[str, Any]:
        """Map enum fields that map to multiple PW fields."""
        config = self.field_config.ENUM_FIELDS[field_name]

        if not value:
            return {field: "" for field in config.values}

        if field_name == "projectClass":
            return self._map_project_class_field(value, config.values)
        elif field_name == "projectDistrict":
            return self._map_project_district_field(value, config.values)
        elif field_name == "personPlanning":
            return self._map_person_planning_field(value, config.values)
        elif field_name == "personConstruction":
            return self._map_person_construction_field(value, config.values)
        else:
            logger.warning(f"Unsupported enum field '{field_name}'")
            return {}

    def _get_service_value(self, field_name: str, value: Any) -> Optional[str]:
        """Get the actual value from the appropriate service."""
        try:
            if field_name == "phase":
                return ProjectPhaseService.get_by_id(value).value if value else None
            elif field_name == "type":
                return ProjectTypeService.get_by_id(value).value if value else None
            elif field_name == "area":
                return ProjectAreaService.get_by_id(value).value if value else None
            elif field_name == "responsibleZone":
                return ResponsibleZoneService.get_by_id(value).value if value else None
            elif field_name == "constructionPhaseDetail":
                return ConstructionPhaseDetailService.get_by_id(value).value if value else None
            else:
                return None
        except Exception as e:
            logger.warning(f"Failed to get service value for '{field_name}': {e}")
            return None

    def _map_project_class_field(self, value: Any, pw_fields: List[str]) -> Dict[str, str]:
        """Map project class to hierarchical PW fields."""
        try:
            classes = ProjectClassService.get_by_id(value).path.split("/") if value else ["", "", ""]
            result = {}
            for i, pw_field in enumerate(pw_fields):
                result[pw_field] = classes[i] if i < len(classes) else ""
            return result
        except Exception as e:
            logger.warning(f"Failed to map project class: {e}")
            return {field: "" for field in pw_fields}

    def _map_project_district_field(self, value: Any, pw_fields: List[str]) -> Dict[str, str]:
        """Map project district to hierarchical PW fields."""
        try:
            locations = ProjectDistrictService.get_by_id(value).path.split("/") if value else ["", "", ""]
            result = {}
            for i, pw_field in enumerate(pw_fields):
                result[pw_field] = locations[i] if i < len(locations) else ""
            return result
        except Exception as e:
            logger.warning(f"Failed to map project district: {e}")
            return {field: "" for field in pw_fields}

    def _map_person_planning_field(self, value: Any, pw_fields: List[str]) -> Dict[str, str]:
        """Map planning person to multiple PW fields."""
        try:
            person = PersonService.get_by_id(value) if value else None
            if not person:
                return {field: "" for field in pw_fields}

            return {
                pw_fields[0]: f"{person.lastName} {person.firstName}",
                pw_fields[1]: person.title or "",
                pw_fields[2]: person.phone or "",
                pw_fields[3]: person.email or "",
            }
        except Exception as e:
            logger.warning(f"Failed to map planning person: {e}")
            return {field: "" for field in pw_fields}

    def _map_person_construction_field(self, value: Any, pw_fields: List[str]) -> Dict[str, str]:
        """Map construction person to PW field."""
        try:
            person = PersonService.get_by_id(value) if value else None
            if not person:
                return {pw_fields[0]: ""}

            full_info = f"{person.lastName}, {person.firstName}, {person.title}, {person.phone}, {person.email}"
            return {pw_fields[0]: full_info}
        except Exception as e:
            logger.warning(f"Failed to map construction person: {e}")
            return {pw_fields[0]: ""}



def create_comprehensive_project_data(project: Project) -> dict:
    """
    Create comprehensive project data for ProjectWise sync.

    Args:
        project: Project object to extract data from

    Returns:
        Dictionary with project data for PW sync
    """
    data = {}

    # Basic fields
    if project.name is not None:
        data['name'] = project.name
    if project.address is not None:
        data['address'] = project.address
    if project.description is not None:
        data['description'] = project.description
    if project.entityName is not None:
        data['entityName'] = project.entityName

    # Boolean fields
    if project.programmed is not None:
        data['programmed'] = project.programmed
    if project.gravel is not None:
        data['gravel'] = project.gravel
    if project.louhi is not None:
        data['louhi'] = project.louhi

    # Integer fields
    if project.planningStartYear is not None:
        data['planningStartYear'] = project.planningStartYear
    if project.constructionEndYear is not None:
        data['constructionEndYear'] = project.constructionEndYear

    # Date fields
    if project.estPlanningStart is not None:
        data['estPlanningStart'] = project.estPlanningStart
    if project.estPlanningEnd is not None:
        data['estPlanningEnd'] = project.estPlanningEnd
    if project.presenceStart is not None:
        data['presenceStart'] = project.presenceStart
    if project.presenceEnd is not None:
        data['presenceEnd'] = project.presenceEnd
    if project.visibilityStart is not None:
        data['visibilityStart'] = project.visibilityStart
    if project.visibilityEnd is not None:
        data['visibilityEnd'] = project.visibilityEnd
    if project.estConstructionStart is not None:
        data['estConstructionStart'] = project.estConstructionStart
    if project.estConstructionEnd is not None:
        data['estConstructionEnd'] = project.estConstructionEnd

    # List value fields
    if project.phase is not None:
        data['phase'] = str(project.phase.id) if hasattr(project.phase, 'id') else str(project.phase)
    if project.type is not None:
        data['type'] = str(project.type.id) if hasattr(project.type, 'id') else str(project.type)
    if project.area is not None:
        data['area'] = str(project.area.id) if hasattr(project.area, 'id') else str(project.area)
    if project.responsibleZone is not None:
        data['responsibleZone'] = str(project.responsibleZone.id) if hasattr(project.responsibleZone, 'id') else str(project.responsibleZone)
    if project.constructionPhaseDetail is not None:
        data['constructionPhaseDetail'] = str(project.constructionPhaseDetail.id) if hasattr(project.constructionPhaseDetail, 'id') else str(project.constructionPhaseDetail)

    # Enum fields
    if project.projectDistrict is not None:
        data['projectDistrict'] = str(project.projectDistrict.id) if hasattr(project.projectDistrict, 'id') else str(project.projectDistrict)
    if project.projectClass is not None:
        data['projectClass'] = str(project.projectClass.id) if hasattr(project.projectClass, 'id') else str(project.projectClass)
    if project.personPlanning is not None:
        data['personPlanning'] = str(project.personPlanning.id) if hasattr(project.personPlanning, 'id') else str(project.personPlanning)
    if project.personConstruction is not None:
        data['personConstruction'] = str(project.personConstruction.id) if hasattr(project.personConstruction, 'id') else str(project.personConstruction)

    # Additional fields
    if project.masterPlanAreaNumber is not None:
        data['masterPlanAreaNumber'] = project.masterPlanAreaNumber
    if project.trafficPlanNumber is not None:
        data['trafficPlanNumber'] = project.trafficPlanNumber
    if project.bridgeNumber is not None:
        data['bridgeNumber'] = project.bridgeNumber

    return data
