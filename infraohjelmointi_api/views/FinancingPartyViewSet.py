from rest_framework import status, viewsets
from rest_framework.response import Response

from infraohjelmointi_api.models.ConstructionHandoverFinancing import FinancingParty
from infraohjelmointi_api.serializers.FinancingPartySerializer import FinancingPartySerializer
from .BaseViewSet import BaseViewSet


class FinancingPartyViewSet(viewsets.ViewSet):
    """API endpoint for financing parties (dropdown data).

    Built from a code enum, so there is nothing to cache.
    """

    permission_classes = BaseViewSet.permission_classes
    authentication_classes = BaseViewSet.authentication_classes
    http_method_names = ["get"]

    def list(self, request):
        data = [{"id": choice.value, "value": choice.label} for choice in FinancingParty]
        return Response(FinancingPartySerializer(data, many=True).data)

    def retrieve(self, request, pk=None):
        # Keep this endpoint list-only, matching option lookup usage in the UI.
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
