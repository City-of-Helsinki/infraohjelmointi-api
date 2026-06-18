# === PHASE MAPPINGS ===
PHASE_MAP_FOR_PW = {
    "proposal": "1. Hanke-ehdotus",
    "design": "1.5 Yleissuunnittelu",
    "programming": "2. Ohjelmointi",
    # IO-863: draftInitiation/draftApproval/constructionPlan were merged into one
    # `planning` ("Suunnittelu") phase (migration 0109). These keys are kept on
    # purpose: no project references them post-migration (so the outbound mapper
    # never hits them) and the reverse map is still used by tests. A live
    # `planning` -> PW label mapping is DEFERRED until PW admins create the value
    # on the PW side; an unmapped `planning` phase safely DEBUG-skips meanwhile.
    # "planning": "<PW label TBD>",
    "draftInitiation": [
        "3. Suunnittelun aloitus / Suunnitelmaluonnos",
        "3. Katu- ja puistosuunnittelun aloitus/suunnitelmaluonnos",
    ],
    "draftApproval": "4. Katu- / puistosuunnitelmaehdotus ja hyväksyminen",
    "constructionPlan": "5. Rakennussuunnitelma",
    "constructionWait": "6. Odottaa rakentamista",
    "constructionPreparation": "6.5 Rakentamisen valmistelu",
    "construction": "7. Rakentaminen",
    "warrantyPeriod": "8. Takuuaika",
    "completed": "9. Valmis / ylläpidossa",
    "suspended": "10. Keskeytetty toistaiseksi",
}

PHASE_MAP_FOR_INFRATOOL = {
    "proposal": "1. Hanke-ehdotus",
    "design": "1.5 Yleissuunnittelu",
    "programming": "2. Ohjelmointi",
    # IO-863: merged into `planning`; kept for the reverse map. See PHASE_MAP_FOR_PW.
    # "planning": "<PW label TBD>",
    "draftInitiation": "3. Katu- ja puistosuunnittelun aloitus/suunnitelmaluonnos",
    "draftApproval": "4. Katu- / puistosuunnitelmaehdotus ja hyväksyminen",
    "constructionPlan": "5. Rakennussuunnitelma",
    "constructionWait": "6. Odottaa rakentamista",
    "constructionPreparation": "6.5 Rakentamisen valmistelu",
    "construction": "7. Rakentaminen",
    "warrantyPeriod": "8. Takuuaika",
    "completed": "9. Valmis / ylläpidossa",
    "suspended": "10. Keskeytetty toistaiseksi",
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

# === PROJECT PHASE DETAIL MAPPINGS (values that exist in ProjectWise) ===
# IO-863: all the new programming/planning/construction/warranty details are
# DEFERRED pending ProjectWise admins creating the matching picklist values on the
# PW side. They are left unmapped on purpose so the sync layer DEBUG-skips them
# (see ProjectWiseDataMapper._map_list_field) instead of pushing a value PW may
# reject. Re-enable each line once PW confirms the value exists:
#   programming                     -> "Ohjelmointi"
#   waitingProjectManager           -> "Odottaa suunnittelun projektipäällikön nimeämistä"
#   waitingPlanningStart            -> "Odottaa suunnittelun käynnistämistä, projektipäällikkö nimetty"
#   firstPhaseCompleteOrIncomplete  -> "Ensimmäinen vaihe valmis/keskeneräinen"
#   otherReason                     -> "Muu syy"
#   constructionStage               -> "Rakentaminen"
#   warranty                        -> "Takuuaika"
#   warrantyIncomplete              -> "Takuuaika/keskeneräinen"
#
# movedToConstruction: IO-863 relabels it "Siirretty rakennuttamiseen" (UI) and moves
# it under "Odottaa rakentamista". The PW label here is kept as the existing
# "Siirretty rakentamiseen" so sync keeps working; once PW renames it (and confirms it
# valid under "Odottaa rakentamista"), update this value. firstPhaseComplete is dead
# after migration 0109 (harmless).
PHASE_DETAILS_MAP_FOR_PW = {
    "preConstruction": "1. Esirakentaminen",
    "firstPhase": "2. Ensimmäinen vaihe",
    "firstPhaseComplete": "3. Ensimmäinen vaihe valmis",
    "secondPhase": "4. Toinen vaihe / viimeistely",
    "movedToConstruction": "Siirretty rakentamiseen",
    "contractPreparation": "Urakan valmistelu",
    # DEFERRED pending PW admins (see note above) — keep unmapped so they DEBUG-skip:
    # "programming": "Ohjelmointi",
    # "waitingProjectManager": "Odottaa suunnittelun projektipäällikön nimeämistä",
    # "waitingPlanningStart": "Odottaa suunnittelun käynnistämistä, projektipäällikkö nimetty",
}

# === FIELD MAPPER LOOKUP ===
FIELD_MAPPER_LOOKUP = {
    "phase_map_for_infratool": PHASE_MAP_FOR_INFRATOOL,
    "project_type_map": PROJECT_TYPE_MAP,
    "project_area_map": PROJECT_AREA_MAP,
    "responsible_zone_map": RESPONSIBLE_ZONE_MAP,
    "construction_phase_details_map": PHASE_DETAILS_MAP_FOR_PW,
}
