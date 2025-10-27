# === PHASE MAPPINGS ===
PHASE_MAP_FOR_PW = {
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

PHASE_MAP_FOR_INFRATOOL = {
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

# === PROJECT AREA MAPPINGS ===
PROJECT_AREA_MAP = {
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

# === RESPONSIBLE ZONE MAPPINGS ===
RESPONSIBLE_ZONE_MAP = {
    "east": "Itä",
    "west": "Länsi",
    "north": "Pohjoinen",
    "variousAreas": "Eri alueita",
}

# === PROJECT TYPE MAPPINGS ===
PROJECT_TYPE_MAP = {
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

# === CONSTRUCTION PHASE DETAIL MAPPINGS ===
CONSTRUCTION_PHASE_DETAILS_MAP = {
    "preConstruction": "1. Esirakentaminen",
    "firstPhase": "2. Ensimmäinen vaihe",
    "firstPhaseComplete": "3. Ensimmäinen vaihe valmis",
    "secondPhase": "4. Toinen vaihe / viimeistely",
}

# === FIELD MAPPER LOOKUP ===
FIELD_MAPPER_LOOKUP = {
    "phase_map_for_infratool": PHASE_MAP_FOR_INFRATOOL,
    "project_type_map": PROJECT_TYPE_MAP,
    "project_area_map": PROJECT_AREA_MAP,
    "responsible_zone_map": RESPONSIBLE_ZONE_MAP,
    "construction_phase_details_map": CONSTRUCTION_PHASE_DETAILS_MAP,
}
