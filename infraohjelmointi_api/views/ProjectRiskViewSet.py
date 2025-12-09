from infraohjelmointi_api.serializers.ProjectRiskSerializer import ProjectRiskSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectRiskViewSet(CachedLookupViewSet):
    """API endpoint for project risks (cached)."""

    serializer_class = ProjectRiskSerializer
