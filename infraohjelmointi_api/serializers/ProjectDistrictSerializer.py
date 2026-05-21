import logging

from rest_framework import serializers

from infraohjelmointi_api.models import ProjectDistrict
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.ProjectProgrammerSerializer import (
    ProjectProgrammerSerializer,
)
from infraohjelmointi_api.utils.project_class_utils import (
    build_location_programmer_lookup,
    get_programmer_from_name_hierarchy,
)

logger = logging.getLogger(__name__)

# Shared with ProjectLocationSerializer so a single request builds the
# {name: ProjectProgrammer} table only once across both serializers.
_LOOKUP_CONTEXT_KEY = "_default_programmer_by_class_name"


class ProjectDistrictSerializer(serializers.ModelSerializer):
    """
    The project form's location dropdowns are backed by ``GET /project-districts/``,
    so the IO-411 default-programmer preview lives here for the UI to consume
    before save. ``computedDefaultProgrammer`` walks the district ``parent``
    chain and matches each level's name against a programmer-view ``ProjectClass``.
    """

    computedDefaultProgrammer = serializers.SerializerMethodField()

    class Meta(BaseMeta):
        model = ProjectDistrict

    def _get_name_lookup(self):
        cached = self.context.get(_LOOKUP_CONTEXT_KEY)
        if cached is not None:
            return cached
        lookup = build_location_programmer_lookup()
        try:
            self.context[_LOOKUP_CONTEXT_KEY] = lookup
        except TypeError:
            # Frozen mapping (e.g. MappingProxyType): rebuilding per row is
            # still cheaper than per-row queries.
            pass
        return lookup

    def get_computedDefaultProgrammer(self, obj):
        try:
            programmer = get_programmer_from_name_hierarchy(
                obj, name_lookup=self._get_name_lookup()
            )
            if programmer:
                return ProjectProgrammerSerializer(programmer).data
            return None
        except ValueError as e:
            logger.error(f"District hierarchy error: {e}")
            return None
