from infraohjelmointi_api.serializers.ConstructionPhaseSerializer import ConstructionPhaseSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ConstructionPhaseViewSet(CachedLookupViewSet):
    """API endpoint for construction phases (cached)."""

    serializer_class = ConstructionPhaseSerializer
