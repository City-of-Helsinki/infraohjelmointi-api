BASIC_INFO_REQUIRED_FIELDS = (
    "projectName", "district", "projectProgrammeCompiler", "summary",
)
BRIEF_BASIC_INFO_REQUIRED_FIELDS = BASIC_INFO_REQUIRED_FIELDS + ("estimatedCosts",)
EXTENDED_BASIC_INFO_REQUIRED_FIELDS = BASIC_INFO_REQUIRED_FIELDS + (
    "personsInvolved", "strategyGoals", "costClass", "projectSize", "risks",
    "studyAndPlanningNeeds", "planningAndImplementationFeasibility",
)
SECTION_REQUIRED_FIELDS = {
    "designCriteria": (
        "relationshipToPublicAreaServices", "siteValuesProtectionAndSignificance",
    ),
    "trafficPlanningCriteria": (
        "targetTrafficChanges", "pedestrianTraffic", "bicycleTraffic", "carTraffic",
        "serviceAndPickupTraffic", "otherTraffic", "accessibility", "noiseManagement",
        "winterMaintenance",
    ),
    "urbanSpacingPlanningCriteria": (
        "targetUrbanAppearance", "surfaceMaterials", "structures",
        "technicalNetworksAndSystems", "lighting", "greenery",
        "lumoConsiderationAndProtection", "natureTypes", "equipmentAndFurnishings",
        "waters", "stormwaterManagement",
    ),
    "maintenanceNeeds": ("maintenanceNeeds",),
    "interactionAndRelatedProjects": ("collaborationAndExperts", "interactionNotes"),
}


def get_required_section_fields(programme):
    is_brief = programme.briefProjectProgramme is not False
    fields = {
        "basicInfo": (
            BRIEF_BASIC_INFO_REQUIRED_FIELDS
            if is_brief else EXTENDED_BASIC_INFO_REQUIRED_FIELDS
        ),
    }
    if not is_brief:
        fields.update(SECTION_REQUIRED_FIELDS)
    return fields


def get_missing_required_fields(programme, section_name=None):
    required_fields = get_required_section_fields(programme)
    if section_name is not None:
        required_fields = {
            section_name: required_fields.get(
                section_name, SECTION_REQUIRED_FIELDS.get(section_name, ())
            ),
        }

    errors = {}
    for relation_name, fields in required_fields.items():
        section = getattr(programme, relation_name, None)
        if section_name is None and getattr(section, "status", None) == "COMPLETE":
            continue
        missing = {}
        for field in fields:
            value = getattr(section, field, None)
            if not isinstance(value, str) or not value.strip():
                missing[field] = ["This field is required."]
        if missing:
            errors[relation_name] = missing
    return errors