from rest_framework import status, viewsets
from rest_framework.response import Response

from infraohjelmointi_api.models.ConstructionHandoverFinancing import FinancingParty
from infraohjelmointi_api.serializers.FinancingPartySerializer import FinancingPartySerializer
from infraohjelmointi_api.services.CacheService import CacheService
from .BaseViewSet import BaseViewSet


class FinancingPartyViewSet(viewsets.ViewSet):
    """API endpoint for financing parties (dropdown data)."""

    permission_classes = BaseViewSet.permission_classes
    authentication_classes = BaseViewSet.authentication_classes
    http_method_names = ["get"]

    def get_cache_key_name(self) -> str:
        return "FinancingParty"

    def _get_lookup_data(self):
        return [{"id": choice.value, "value": choice.label} for choice in FinancingParty]

    def list(self, request):
        cache_key = self.get_cache_key_name()
        cached_data = CacheService.get_lookup(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        serializer = FinancingPartySerializer(self._get_lookup_data(), many=True)
        CacheService.set_lookup(cache_key, serializer.data)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        # Keep this endpoint list-only, matching option lookup usage in the UI.
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
