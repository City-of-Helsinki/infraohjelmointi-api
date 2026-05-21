from infraohjelmointi_api.serializers.StaraProcurementReasonSerializer import StaraProcurementReasonSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class StaraProcurementReasonViewSet(CachedLookupViewSet):
    """API endpoint for stara procurement reasons (cached)."""

    serializer_class = StaraProcurementReasonSerializer
    project_field = 'staraProcurementReason'


