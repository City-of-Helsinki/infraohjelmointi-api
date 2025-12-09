from infraohjelmointi_api.serializers.ProjectPrioritySerializer import ProjectPrioritySerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectPriorityViewSet(CachedLookupViewSet):
    """API endpoint for project priorities (cached)."""

    serializer_class = ProjectPrioritySerializer
