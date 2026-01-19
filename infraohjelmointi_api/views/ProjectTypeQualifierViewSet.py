from infraohjelmointi_api.serializers.ProjectTypeQualifierSerializer import ProjectTypeQualifierSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectTypeQualifierViewSet(CachedLookupViewSet):
    """API endpoint for project type qualifiers (cached)."""

    serializer_class = ProjectTypeQualifierSerializer
