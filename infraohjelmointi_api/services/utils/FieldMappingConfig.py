from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class BooleanFieldConfig:
    """Configuration for boolean field mapping."""
    field: str
    true_value: str
    false_value: str


@dataclass
class DateFieldConfig:
    """Configuration for date field mapping."""
    field: str
    from_format: str
    to_format: str


@dataclass
class ListValueFieldConfig:
    """Configuration for list value field mapping."""
    field: str
    mapper: Dict[str, str]


@dataclass
class EnumFieldConfig:
    """Configuration for enum field mapping."""
    values: List[str]


class FieldMappingConfig:
    """Field mapping configuration for ProjectWise integration."""

    # === BASIC FIELDS ===
    BASIC_FIELDS = {
        "name": "PROJECT_Kohde",
        "address": "PROJECT_Kadun_tai_puiston_nimi",
        "description": "PROJECT_Hankkeen_kuvaus",
        "entityName": "PROJECT_Aluekokonaisuuden_nimi",
    }

    # === BOOLEAN FIELDS ===
    BOOLEAN_FIELDS = {
        "programmed": BooleanFieldConfig(
            field="PROJECT_Ohjelmoitu",
            true_value="Kyllä",
            false_value="Ei"
        ),
        "gravel": BooleanFieldConfig(
            field="PROJECT_Sorakatu",
            true_value="Kyllä",
            false_value="Ei"
        ),
        "louhi": BooleanFieldConfig(
            field="PROJECT_Louheen",
            true_value="Kyllä",
            false_value="Ei"
        ),
    }

    # === INTEGER FIELDS ===
    INTEGER_FIELDS = {
        "planningStartYear": "PROJECT_Louhi__hankkeen_aloitusvuosi",
        "constructionEndYear": "PROJECT_Louhi__hankkeen_valmistumisvuosi",
    }

    # === DATE FIELDS ===
    DATE_FIELDS = {
        "estPlanningStart": DateFieldConfig(
            field="PROJECT_Hankkeen_suunnittelu_alkaa",
            from_format="%d.%m.%Y",
            to_format="%Y-%m-%dT%H:%M:%S"
        ),
        "estPlanningEnd": DateFieldConfig(
            field="PROJECT_Hankkeen_suunnittelu_pttyy",
            from_format="%d.%m.%Y",
            to_format="%Y-%m-%dT%H:%M:%S"
        ),
        "presenceStart": DateFieldConfig(
            field="PROJECT_Esillaolo_alku",
            from_format="%d.%m.%Y",
            to_format="%Y-%m-%dT%H:%M:%S"
        ),
        "presenceEnd": DateFieldConfig(
            field="PROJECT_Esillaolo_loppu",
            from_format="%d.%m.%Y",
            to_format="%Y-%m-%dT%H:%M:%S"
        ),
        "visibilityStart": DateFieldConfig(
            field="PROJECT_Nhtvillolo_alku",
            from_format="%d.%m.%Y",
            to_format="%Y-%m-%dT%H:%M:%S"
        ),
        "visibilityEnd": DateFieldConfig(
            field="PROJECT_Nhtvillolo_loppu",
            from_format="%d.%m.%Y",
            to_format="%Y-%m-%dT%H:%M:%S"
        ),
        "estConstructionStart": DateFieldConfig(
            field="PROJECT_Hankkeen_rakentaminen_alkaa",
            from_format="%d.%m.%Y",
            to_format="%Y-%m-%dT%H:%M:%S"
        ),
        "estConstructionEnd": DateFieldConfig(
            field="PROJECT_Hankkeen_rakentaminen_pttyy",
            from_format="%d.%m.%Y",
            to_format="%Y-%m-%dT%H:%M:%S"
        ),
    }

    # === LIST VALUE FIELDS ===
    LIST_VALUE_FIELDS = {
        "phase": ListValueFieldConfig(
            field="PROJECT_Hankkeen_vaihe",
            mapper="phase_map_for_infratool"
        ),
        "type": ListValueFieldConfig(
            field="PROJECT_Toimiala",
            mapper="project_type_map"
        ),
        "area": ListValueFieldConfig(
            field="PROJECT_Projektialue",
            mapper="project_area_map"
        ),
        "responsibleZone": ListValueFieldConfig(
            field="PROJECT_Alue_rakennusviraston_vastuujaon_mukaan",
            mapper="responsible_zone_map"
        ),
        "constructionPhaseDetail": ListValueFieldConfig(
            field="PROJECT_Rakentamisvaiheen_tarkenne",
            mapper="construction_phase_details_map"
        ),
    }

    # === ENUM FIELDS ===
    ENUM_FIELDS = {
        "projectDistrict": EnumFieldConfig(
            values=[
                "PROJECT_Suurpiirin_nimi",
                "PROJECT_Kaupunginosan_nimi",
                "PROJECT_Osa_alue",
            ]
        ),
        "projectClass": EnumFieldConfig(
            values=[
                "PROJECT_Pluokka",
                "PROJECT_Luokka",
                "PROJECT_Alaluokka",
            ]
        ),
        "personPlanning": EnumFieldConfig(
            values=[
                "PROJECT_Vastuuhenkil",
                "PROJECT_Vastuuhenkiln_titteli",
                "PROJECT_Vastuuhenkiln_puhelinnumero",
                "PROJECT_Vastuuhenkiln_shkpostiosoite",
            ]
        ),
        "personConstruction": EnumFieldConfig(
            values=["PROJECT_Vastuuhenkil_rakennuttaminen"]
        ),
    }

    # === FIELD TYPE MAPPINGS ===
    @classmethod
    def get_field_type(cls, field_name: str) -> str:
        """Get the field type for a given field name."""
        if field_name in cls.BASIC_FIELDS:
            return "basic"
        elif field_name in cls.BOOLEAN_FIELDS:
            return "boolean"
        elif field_name in cls.INTEGER_FIELDS:
            return "integer"
        elif field_name in cls.DATE_FIELDS:
            return "date"
        elif field_name in cls.LIST_VALUE_FIELDS:
            return "listvalue"
        elif field_name in cls.ENUM_FIELDS:
            return "enum"
        else:
            return "unsupported"

    @classmethod
    def get_pw_field_name(cls, field_name: str) -> Optional[str]:
        """Get the ProjectWise field name for a given field name."""
        field_type = cls.get_field_type(field_name)

        if field_type == "basic":
            return cls.BASIC_FIELDS[field_name]
        elif field_type == "boolean":
            return cls.BOOLEAN_FIELDS[field_name].field
        elif field_type == "integer":
            return cls.INTEGER_FIELDS[field_name]
        elif field_type == "date":
            return cls.DATE_FIELDS[field_name].field
        elif field_type == "listvalue":
            return cls.LIST_VALUE_FIELDS[field_name].field
        else:
            return None

    @classmethod
    def is_supported_field(cls, field_name: str) -> bool:
        """Check if a field is supported for mapping."""
        return cls.get_field_type(field_name) != "unsupported"
