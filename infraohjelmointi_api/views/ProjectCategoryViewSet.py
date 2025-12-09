from infraohjelmointi_api.serializers.ProjectCategorySerializer import ProjectCategorySerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectCategoryViewSet(CachedLookupViewSet):
    """API endpoint for project categories (cached)."""

    serializer_class = ProjectCategorySerializer

