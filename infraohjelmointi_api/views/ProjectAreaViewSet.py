from infraohjelmointi_api.serializers.ProjectAreaSerializer import ProjectAreaSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectAreaViewSet(CachedLookupViewSet):
    """API endpoint for project areas (cached)."""

    serializer_class = ProjectAreaSerializer
