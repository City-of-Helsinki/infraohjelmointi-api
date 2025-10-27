"""
ProjectWise configuration - all tuneable parameters in one place.
"""


class PWConfig:
    """ProjectWise configuration - all tuneable parameters in one place."""

    # === TIMING (seconds) ===
    HIERARCHICAL_FIELD_DELAY = 0.5  # PW needs time between hierarchical updates
    API_TIMEOUT = 30  # Max time to wait for API response

    # === FIELD CLASSIFICATION ===
    # Protected fields: never overwrite if PW has data
    PROTECTED_FIELDS = frozenset([
        'description',
        'presenceStart',
        'presenceEnd',
        'visibilityStart',
        'visibilityEnd',
        'masterPlanAreaNumber',
        'trafficPlanNumber',
        'bridgeNumber'
    ])

    # Classification fields: special handling for location/class updates
    CLASSIFICATION_FIELDS = frozenset([
        'projectClass',
        'projectDistrict'
    ])

