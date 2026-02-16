from infraohjelmointi_api.serializers.ProjectPhaseDetailSerializer import ProjectPhaseDetailSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectPhaseDetailViewSet(CachedLookupViewSet):
    """API endpoint for project phase details (cached)."""

    serializer_class = ProjectPhaseDetailSerializer
