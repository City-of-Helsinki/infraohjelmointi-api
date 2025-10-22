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

to_pw_map = {
    "name": "PROJECT_Kohde",
    "address": "PROJECT_Kadun_tai_puiston_nimi",
    "description": "PROJECT_Hankkeen_kuvaus",
    "entityName": "PROJECT_Aluekokonaisuuden_nimi",
    "constructionPhaseDetail": "PROJECT_Rakentamisvaiheen_tarkenne",
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
    def convert_to_pw_data(self, data: dict, project: Project):
        result = {}
        for field in data.keys():
            if not field in to_pw_map:
                logger.debug(f"Field '{field}' not supported")
                continue
            value = data[field]
            mapped_field = to_pw_map[field]
            mapped_field_type = type(mapped_field).__name__
            # String value handling
            if mapped_field_type == "str":
                result[mapped_field] = value
            # Boolean to text handling
            elif mapped_field["type"] == "integer":
                logger.debug(f"mapped_field {mapped_field}, value {value}")
                result[mapped_field["field"]] = int(value)

            # Boolean to text handling
            elif mapped_field["type"] == "boolean":
                result[mapped_field["field"]] = mapped_field["values"][
                    str(value).lower()
                ]
            # List value handling
            elif mapped_field["type"] == "listvalue":
                field_mapper = None
                if field == "phase":
                    field_mapper = phase_map_for_infratool
                    value = (
                        ProjectPhaseService.get_by_id(value).value
                        if not value is None
                        else ""
                    )
                elif field == "type":
                    field_mapper = project_type_map
                    value = (
                        ProjectTypeService.get_by_id(value).value
                        if not value is None
                        else ""
                    )
                elif field == "area":
                    field_mapper = project_area_map
                    value = (
                        ProjectAreaService.get_by_id(value).value
                        if not value is None
                        else ""
                    )
                elif field == "responsibleZone":
                    field_mapper = responsible_zone_map
                    value = (
                        ResponsibleZoneService.get_by_id(value).value
                        if not value is None
                        else ""
                    )
                elif field == "constructionPhaseDetail":
                    field_mapper = construction_phase_details_map
                    value = (
                        ConstructionPhaseDetailService.get_by_id(value).value
                        if not value is None
                        else ""
                    )
                else:
                    raise ProjectWiseDataFieldNotFound(f"Field '{field}' not supported")

                result[mapped_field["field"]] = field_mapper[value] if value else None
            # Class/Location field handling
            elif mapped_field["type"] == "enum":
                if field == "projectClass":
                    classes = (
                        ProjectClassService.get_by_id(value).path.split("/")
                        if not value is None
                        else ["", "", ""]
                    )
                    result[mapped_field["values"][0]] = classes[0]
                    if len(classes) > 1:
                        result[mapped_field["values"][1]] = classes[1]
                    if len(classes) > 2:
                        result[mapped_field["values"][2]] = classes[2]
                elif field == "projectDistrict":
                    locations = (
                        ProjectDistrictService.get_by_id(value).path.split("/")
                        if not value is None
                        else ["", "", ""]
                    )
                    result[mapped_field["values"][0]] = locations[0]
                    if len(locations) > 1:
                        result[mapped_field["values"][1]] = locations[1]
                    if len(locations) > 2:
                        result[mapped_field["values"][2]] = locations[2]
                elif field == "personPlanning":
                    planningPersonModel = PersonService.get_by_id(value) if value else None
                    # fullname
                    result[mapped_field["values"][0]] = "{} {}".format(
                        planningPersonModel.lastName, planningPersonModel.firstName
                    ) if planningPersonModel else ""
                    # title
                    result[mapped_field["values"][1]] = planningPersonModel.title if planningPersonModel else ""
                    # phone
                    result[mapped_field["values"][2]] = planningPersonModel.phone if planningPersonModel else ""
                    # email
                    result[mapped_field["values"][3]] = planningPersonModel.email if planningPersonModel else ""
                elif field == "personConstruction":
                    constructionPersonModel = PersonService.get_by_id(value) if value else None
                    # fullname
                    result[mapped_field["values"][0]] = "{} {}, {}, {}, {}".format(
                        constructionPersonModel.lastName,
                        constructionPersonModel.firstName,
                        constructionPersonModel.title,
                        constructionPersonModel.phone,
                        constructionPersonModel.email,
                    ) if constructionPersonModel else ""

            # Date field handling
            elif mapped_field["type"] == "date":
                if value:
                    if isinstance(value, str):
                        result[mapped_field["field"]] = datetime.strptime(
                            value,
                            mapped_field["fromFormat"],
                        ).strftime(mapped_field["toFormat"])
                    elif isinstance(value, datetime):
                        result[mapped_field["field"]] = value.strftime(mapped_field["toFormat"])
                    elif hasattr(value, 'year'):  # Handle datetime.date objects
                        # Convert date to datetime with midnight time, then format
                        dt = datetime.combine(value, datetime.min.time())
                        result[mapped_field["field"]] = dt.strftime(mapped_field["toFormat"])
                    else:
                        result[mapped_field["field"]] = ""
                else:
                    result[mapped_field["field"]] = ""
            else:
                raise ProjectWiseDataFieldNotFound(f"Field '{field}' not supported")

        return result

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
    Create comprehensive project data for ProjectWise synchronization.
    
    Args:
        project: The project object to extract data from
        
    Returns:
        Dictionary with project fields (internal field names), excluding None values
    """
    comprehensive_data = {
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

    return {k: v for k, v in comprehensive_data.items() if v is not None}


class ProjectWiseDataFieldNotFound(RuntimeError):
    """Error for not supporting field"""

    pass
