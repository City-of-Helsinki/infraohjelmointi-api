from infraohjelmointi_api.serializers.ConstructionProcurementMethodSerializer import ConstructionProcurementMethodSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class ConstructionProcurementMethodViewSet(CachedLookupViewSet):
    """API endpoint for construction procurement methods (cached)."""

    serializer_class = ConstructionProcurementMethodSerializer


