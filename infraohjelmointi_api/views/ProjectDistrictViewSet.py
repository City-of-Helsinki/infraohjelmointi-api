from infraohjelmointi_api.models import ProjectClass, ProjectDistrict, ProjectProgrammer
from infraohjelmointi_api.serializers.ProjectDistrictSerializer import (
    ProjectDistrictSerializer,
)

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectDistrictViewSet(CachedLookupViewSet):
    """API endpoint for project districts (cached)."""

    serializer_class = ProjectDistrictSerializer
    # computedDefaultProgrammer (IO-411) comes from the programmer-view classes'
    # defaultProgrammer.
    cache_depends_on = (ProjectClass, ProjectProgrammer)

    def get_queryset(self):
        # Pre-load the parent chain (district → division → subDivision) so
        # serializing computedDefaultProgrammer doesn't issue per-row queries.
        return (
            ProjectDistrict.objects.all()
            .select_related("parent", "parent__parent", "parent__parent__parent")
        )
