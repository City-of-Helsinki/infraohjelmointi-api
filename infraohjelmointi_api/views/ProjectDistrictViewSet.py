from infraohjelmointi_api.serializers.ProjectDistrictSerializer import ProjectDistrictSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectDistrictViewSet(CachedLookupViewSet):
    """API endpoint for project districts (cached)."""

    serializer_class = ProjectDistrictSerializer
