from infraohjelmointi_api.serializers.ProjectTypeSerializer import ProjectTypeSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectTypeViewSet(CachedLookupViewSet):
    """API endpoint for project types (cached)."""

    serializer_class = ProjectTypeSerializer
