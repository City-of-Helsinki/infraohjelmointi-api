from infraohjelmointi_api.serializers.ProjectQualityLevelSerializer import ProjectQualityLevelSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectQualityLevelViewSet(CachedLookupViewSet):
    """API endpoint for project quality levels (cached)."""

    serializer_class = ProjectQualityLevelSerializer
