from infraohjelmointi_api.models import ProjectDistrict
from infraohjelmointi_api.serializers.ProjectDistrictSerializer import (
    ProjectDistrictSerializer,
)

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectDistrictViewSet(CachedLookupViewSet):
    """API endpoint for project districts (cached)."""

    serializer_class = ProjectDistrictSerializer

    # Bump on response-shape changes so post-deploy clients hit a cold cache
    # instead of stale Redis entries missing computedDefaultProgrammer (IO-411).
    _CACHE_KEY_VERSION = "v2-io411"

    def get_cache_key_name(self) -> str:
        return f"{super().get_cache_key_name()}:{self._CACHE_KEY_VERSION}"

    def get_queryset(self):
        # Pre-load the parent chain (district → division → subDivision) so
        # serializing computedDefaultProgrammer doesn't issue per-row queries.
        return (
            ProjectDistrict.objects.all()
            .select_related("parent", "parent__parent", "parent__parent__parent")
        )
