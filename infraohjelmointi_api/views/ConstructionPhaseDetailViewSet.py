from infraohjelmointi_api.serializers.ConstructionPhaseDetailSerializer import ConstructionPhaseDetailSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ConstructionPhaseDetailViewSet(CachedLookupViewSet):
    """API endpoint for construction phase details (cached)."""

    serializer_class = ConstructionPhaseDetailSerializer
