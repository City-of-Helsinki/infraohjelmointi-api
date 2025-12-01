from infraohjelmointi_api.serializers.ProjectPhaseSerializer import ProjectPhaseSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectPhaseViewSet(CachedLookupViewSet):
    """API endpoint for project phases (cached)."""

    serializer_class = ProjectPhaseSerializer
