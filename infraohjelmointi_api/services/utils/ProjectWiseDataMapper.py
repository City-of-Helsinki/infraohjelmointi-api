from infraohjelmointi_api.services import ProjectDistrictService
from ...models import Project
from ..ProjectAreaService import ProjectAreaService
from ..ProjectPhaseService import ProjectPhaseService
from ..ResponsibleZoneService import ResponsibleZoneService
from ..ProjectTypeService import ProjectTypeService
from ..ConstructionPhaseDetailService import ConstructionPhaseDetailService
from ..ProjectClassService import ProjectClassService
from ..PersonService import PersonService

import logging

from datetime import datetime

logger = logging.getLogger("infraohjelmointi_api")

"""
Maps infra tool fields to ProjectWise API fields.
Handles type conversions, value lookups, and format normalization.
"""
to_pw_map = {
    "name": "PROJECT_Kohde",
    "address": "PROJECT_Kadun_tai_puiston_nimi",
    "description": "PROJECT_Hankkeen_kuvaus",
    "entityName": "PROJECT_Aluekokonaisuuden_nimi",
    "programmed": {
        "field": "PROJECT_Ohjelmoitu",
        "type": "boolean",
        "values": {"true": "Kyllä", "false": "Ei"},
    },
    "gravel": {
        "field": "PROJECT_Sorakatu",
        "type": "boolean",
        "values": {"true": "Kyllä", "false": "Ei"},
    },
    "louhi": {
        "field": "PROJECT_Louheen",
        "type": "boolean",
        "values": {"true": "Kyllä", "false": "Ei"},
    },
    "planningStartYear": {
        "field": "PROJECT_Louhi__hankkeen_aloitusvuosi",
        "type": "integer",
    },
    "constructionEndYear": {
        "field": "PROJECT_Louhi__hankkeen_valmistumisvuosi",
        "type": "integer",
    },
    "estPlanningStart": {
        "field": "PROJECT_Hankkeen_suunnittelu_alkaa",
        "type": "date",
        "fromFormat": "%d.%m.%Y",
        "toFormat": "%Y-%m-%dT%H:%M:%S",
    },
    "estPlanningEnd": {
        "field": "PROJECT_Hankkeen_suunnittelu_pttyy",
        "type": "date",
        "fromFormat": "%d.%m.%Y",
        "toFormat": "%Y-%m-%dT%H:%M:%S",
    },
    "presenceStart": {
        "field": "PROJECT_Esillaolo_alku",
        "type": "date",
        "fromFormat": "%d.%m.%Y",
        "toFormat": "%Y-%m-%dT%H:%M:%S",
    },
    "presenceEnd": {
        "field": "PROJECT_Esillaolo_loppu",
        "type": "date",
        "fromFormat": "%d.%m.%Y",
        "toFormat": "%Y-%m-%dT%H:%M:%S",
    },
    "visibilityStart": {
        "field": "PROJECT_Nhtvillolo_alku",
        "type": "date",
        "fromFormat": "%d.%m.%Y",
        "toFormat": "%Y-%m-%dT%H:%M:%S",
    },
    "visibilityEnd": {
        "field": "PROJECT_Nhtvillolo_loppu",
        "type": "date",
        "fromFormat": "%d.%m.%Y",
        "toFormat": "%Y-%m-%dT%H:%M:%S",
    },
    "estConstructionStart": {
        "field": "PROJECT_Hankkeen_rakentaminen_alkaa",
        "type": "date",
        "fromFormat": "%d.%m.%Y",
        "toFormat": "%Y-%m-%dT%H:%M:%S",
    },
    "estConstructionEnd": {
        "field": "PROJECT_Hankkeen_rakentaminen_pttyy",
        "type": "date",
        "fromFormat": "%d.%m.%Y",
        "toFormat": "%Y-%m-%dT%H:%M:%S",
    },
    "phase": {"field": "PROJECT_Hankkeen_vaihe", "type": "listvalue"},
    "type": {"field": "PROJECT_Toimiala", "type": "listvalue"},
    "area": {"field": "PROJECT_Projektialue", "type": "listvalue"},
    "responsibleZone": {
        "field": "PROJECT_Alue_rakennusviraston_vastuujaon_mukaan",
        "type": "listvalue",
    },
    "constructionPhaseDetail": {
        "field": "PROJECT_Rakentamisvaiheen_tarkenne",
        "type": "listvalue",
    },
    "projectDistrict": {
        "type": "enum",
        "values": [
            "PROJECT_Suurpiirin_nimi",
            "PROJECT_Kaupunginosan_nimi",
            "PROJECT_Osa_alue",
        ],
    },
    "projectClass": {
        "type": "enum",
        "values": [
            "PROJECT_Pluokka",
            "PROJECT_Luokka",
            "PROJECT_Alaluokka",
        ],
    },
    "personPlanning": {
        "type": "enum",
        "values": [
            "PROJECT_Vastuuhenkil",
            "PROJECT_Vastuuhenkiln_titteli",
            "PROJECT_Vastuuhenkiln_puhelinnumero",
            "PROJECT_Vastuuhenkiln_shkpostiosoite",
        ],
    },
    "personConstruction": {
        "type": "enum",
        "values": ["PROJECT_Vastuuhenkil_rakennuttaminen"],
    },
}

phase_map_for_pw = {
    "proposal": "1. Hanke-ehdotus",
    "design": "1.5 Yleissuunnittelu",
    "programming": "2. Ohjelmointi",
    "draftInitiation": [
        "3. Suunnittelun aloitus / Suunnitelmaluonnos",
        "3. Katu- ja puistosuunnittelun aloitus/suunnitelmaluonnos",
    ],
    "draftApproval": "4. Katu- / puistosuunnitelmaehdotus ja hyväksyminen",
    "constructionPlan": "5. Rakennussuunnitelma",
    "constructionWait": "6. Odottaa rakentamista",
    "construction": "7. Rakentaminen",
    "warrantyPeriod": "8. Takuuaika",
    "completed": "9. Valmis / ylläpidossa",
}

phase_map_for_infratool = {
    "proposal": "1. Hanke-ehdotus",
    "design": "1.5 Yleissuunnittelu",
    "programming": "2. Ohjelmointi",
    "draftInitiation": "3. Katu- ja puistosuunnittelun aloitus/suunnitelmaluonnos",
    "draftApproval": "4. Katu- / puistosuunnitelmaehdotus ja hyväksyminen",
    "constructionPlan": "5. Rakennussuunnitelma",
    "constructionWait": "6. Odottaa rakentamista",
    "construction": "7. Rakentaminen",
    "warrantyPeriod": "8. Takuuaika",
    "completed": "9. Valmis / ylläpidossa",
}

project_area_map = {
    "honkasuo": "Honkasuo",
    "kalasatama": "Kalasatama",
    "kruunuvuorenranta": "Kruunuvuorenranta",
    "kuninkaantammi": "Kuninkaantammi",
    "lansisatama": "Länsisatama",
    "malminLentokenttaalue": "Malmin lentokenttäalue",
    "pasila": "Pasila",
    "ostersundom": "Östersundom",
    "kamppiToolonlahti": "Kamppi-Töölönlahti",
    "kuninkaankolmio": "Kuninkaankolmio",
    "uudetProjektialueetJaMuuTaydennysrakentaminen": "Uudet projektialueet ja muu täydennysrakentaminen",
    "lantinenBulevardikaupunki": "Läntinen bulevardikaupunki",
    "makasiiniranta": "Makasiiniranta",
    "koivusaari": "Koivusaari",
}

responsible_zone_map = {
    "east": "Itä",
    "west": "Länsi",
    "north": "Pohjoinen",
    "variousAreas": "Eri alueita",
}

project_type_map = {
    "projectComplex": "hankekokonaisuus",
    "street": "katu",
    "cityRenewal": "kaupunkiuudistus",
    "traffic": "liikenne",
    "sports": "liikunta",
    "omaStadi": "OmaStadi-hanke",
    "projectArea": "projektialue",
    "park": "puisto",
    "bigTrafficProjects": "suuret liikennehankealueet",
    "spesialtyStructures": "taitorakenne",
    "preConstruction": "esirakentaminen",
}

construction_phase_details_map = {
    "preConstruction": "1. Esirakentaminen",
    "firstPhase": "2. Ensimmäinen vaihe",
    "firstPhaseComplete": "3. Ensimmäinen vaihe valmis",
    "secondPhase": "4. Toinen vaihe / viimeistely",
}


class ProjectWiseDataMapper:
    """Maps infra tool data to PW API format with type conversions and lookups."""

    def convert_to_pw_data(self, data: dict) -> dict:
        """Convert infra tool data dict to PW API format."""
        result = {}
        for field in data.keys():
            if field not in to_pw_map:
                logger.debug(f"Field '{field}' not supported")
                continue

            value = data[field]
            mapped_field = to_pw_map[field]

            self._convert_field(field, value, mapped_field, result)

        return result

    def _convert_field(self, field: str, value, mapped_field, result: dict):
        """Convert a single field based on its type."""
        if isinstance(mapped_field, str):
            result[mapped_field] = value
            return

        field_type = mapped_field.get("type")
        if field_type == "integer":
            self._convert_integer_field(mapped_field, value, result)
        elif field_type == "boolean":
            self._convert_boolean_field(mapped_field, value, result)
        elif field_type == "listvalue":
            self._convert_listvalue_field(field, mapped_field, value, result)
        elif field_type == "enum":
            self._convert_enum_field(field, mapped_field, value, result)
        elif field_type == "date":
            self._convert_date_field(mapped_field, value, result)
        else:
            raise ProjectWiseDataFieldNotFound(f"Field '{field}' type '{field_type}' not supported")

    def _convert_integer_field(self, mapped_field: dict, value, result: dict):
        """Convert integer field."""
        logger.debug(f"mapped_field {mapped_field}, value {value}")
        result[mapped_field["field"]] = int(value)

    def _convert_boolean_field(self, mapped_field: dict, value, result: dict):
        """Convert boolean to Finnish text (Kyllä/Ei)."""
        result[mapped_field["field"]] = mapped_field["values"][str(value).lower()]

    def _convert_listvalue_field(self, field: str, mapped_field: dict, value, result: dict):
        """Convert list value fields with UUID lookup."""
        lookup_map = {
            "phase": (phase_map_for_infratool, ProjectPhaseService),
            "type": (project_type_map, ProjectTypeService),
            "area": (project_area_map, ProjectAreaService),
            "responsibleZone": (responsible_zone_map, ResponsibleZoneService),
            "constructionPhaseDetail": (construction_phase_details_map, ConstructionPhaseDetailService),
        }

        if field not in lookup_map:
            raise ProjectWiseDataFieldNotFound(f"Field '{field}' not supported")

        field_mapper, service = lookup_map[field]
        value = service.get_by_id(value).value if value is not None else ""
        result[mapped_field["field"]] = field_mapper[value] if value else None

    def _convert_enum_field(self, field: str, mapped_field: dict, value, result: dict):
        """Convert enum fields (projectClass, projectDistrict, person)."""
        if field == "projectClass":
            self._convert_project_class(mapped_field, value, result)
        elif field == "projectDistrict":
            self._convert_project_district(mapped_field, value, result)
        elif field == "personPlanning":
            self._convert_person_planning(mapped_field, value, result)
        elif field == "personConstruction":
            self._convert_person_construction(mapped_field, value, result)

    def _convert_project_class(self, mapped_field: dict, value, result: dict):
        """Convert project classification with format normalization."""
        classes = (
            ProjectClassService.get_by_id(value).path.split("/")
            if value is not None
            else ["", "", ""]
        )

        # Normalize "8 04 Description" → "804 Description"
        pluokka = classes[0]
        if pluokka and ' ' in pluokka:
            parts = pluokka.split(' ', 2)
            if (len(parts) >= 2 and
                parts[0].isdigit() and len(parts[0]) == 1 and
                len(parts[1]) >= 2 and parts[1][:2].isdigit()):
                pluokka = parts[0] + parts[1] + (' ' + parts[2] if len(parts) > 2 else '')

        result[mapped_field["values"][0]] = pluokka
        if len(classes) > 1:
            result[mapped_field["values"][1]] = classes[1]
        if len(classes) > 2:
            result[mapped_field["values"][2]] = classes[2]

    def _convert_project_district(self, mapped_field: dict, value, result: dict):
        """Convert project district/location."""
        locations = (
            ProjectDistrictService.get_by_id(value).path.split("/")
            if value is not None
            else ["", "", ""]
        )
        result[mapped_field["values"][0]] = locations[0]
        if len(locations) > 1:
            result[mapped_field["values"][1]] = locations[1]
        if len(locations) > 2:
            result[mapped_field["values"][2]] = locations[2]

    def _convert_person_planning(self, mapped_field: dict, value, result: dict):
        """Convert planning person fields."""
        person = PersonService.get_by_id(value) if value else None
        result[mapped_field["values"][0]] = f"{person.lastName} {person.firstName}" if person else ""
        result[mapped_field["values"][1]] = person.title if person else ""
        result[mapped_field["values"][2]] = person.phone if person else ""
        result[mapped_field["values"][3]] = person.email if person else ""

    def _convert_person_construction(self, mapped_field: dict, value, result: dict):
        """Convert construction person fields."""
        person = PersonService.get_by_id(value) if value else None
        if person:
            result[mapped_field["values"][0]] = f"{person.lastName}, {person.firstName}, {person.title}, {person.phone}, {person.email}"
        else:
            result[mapped_field["values"][0]] = ""

    def _convert_date_field(self, mapped_field: dict, value, result: dict):
        """Convert date fields to PW format."""
        if not value:
            result[mapped_field["field"]] = ""
            return

        if isinstance(value, str):
            dt = datetime.strptime(value, mapped_field["fromFormat"])
            result[mapped_field["field"]] = dt.strftime(mapped_field["toFormat"])
        elif isinstance(value, datetime):
            result[mapped_field["field"]] = value.strftime(mapped_field["toFormat"])
        elif hasattr(value, 'year'):
            dt = datetime.combine(value, datetime.min.time())
            result[mapped_field["field"]] = dt.strftime(mapped_field["toFormat"])
        else:
            result[mapped_field["field"]] = ""

    def load_and_transform_phases(self):
        """Helper method to load phases from DB and transform to match PW format"""
        phases = {}
        for pph in ProjectPhaseService.list_all():
            mapped_value = phase_map_for_pw[pph.value]
            if isinstance(mapped_value, list):
                for key in mapped_value:
                    phases[key] = pph
            else:
                phases[mapped_value] = pph
        return phases

    def load_and_transform_project_areas(self):
        """Helper method to load project areas from DB and transform to match PW format"""

        return {project_area_map[pa.value]: pa for pa in ProjectAreaService.list_all()}

    def load_and_transform_responsible_zones(self):
        """Helper method to load responsible zones from DB and transform to match PW format"""

        return {
            responsible_zone_map[rz.value]: rz
            for rz in ResponsibleZoneService.list_all()
        }

    def load_and_transform_project_types(self):
        """Helper method to load project types from DB and transform to match PW format"""

        return {project_type_map[pt.value]: pt for pt in ProjectTypeService.list_all()}

    def load_and_transform_construction_phase_details(self):
        """Helper method to load construction phase details from DB and transform to match PW format"""

        return {
            construction_phase_details_map[pd.value]: pd
            for pd in ConstructionPhaseDetailService.list_all()
        }


def create_comprehensive_project_data(project: Project) -> dict:
    """
    Create a comprehensive data dictionary for automatic PW updates.

    Args:
        project: The project object to extract data from

    Returns:
        Dictionary with all relevant project fields, excluding None values
    """
    comprehensive_data = {
        'name': project.name,
        'description': project.description,
        'address': project.address,
        'entityName': project.entityName,
        'estPlanningStart': project.estPlanningStart,
        'estPlanningEnd': project.estPlanningEnd,
        'estConstructionStart': project.estConstructionStart,
        'estConstructionEnd': project.estConstructionEnd,
        'presenceStart': project.presenceStart,
        'presenceEnd': project.presenceEnd,
        'visibilityStart': project.visibilityStart,
        'visibilityEnd': project.visibilityEnd,
        'masterPlanAreaNumber': project.masterPlanAreaNumber,
        'trafficPlanNumber': project.trafficPlanNumber,
        'bridgeNumber': project.bridgeNumber,
    }

    # Remove None values to avoid unnecessary processing
    return {k: v for k, v in comprehensive_data.items() if v is not None}


class ProjectWiseDataFieldNotFound(RuntimeError):
    """Error for not supporting field"""

    pass
