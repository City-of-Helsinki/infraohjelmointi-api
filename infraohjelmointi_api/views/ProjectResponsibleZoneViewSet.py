from infraohjelmointi_api.serializers.ProjectResponsibleZoneSerializer import ProjectResponsibleZoneSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ProjectResponsibleZoneViewSet(CachedLookupViewSet):
    """API endpoint for responsible zones (cached)."""

    serializer_class = ProjectResponsibleZoneSerializer
