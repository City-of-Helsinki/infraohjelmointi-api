from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.LocationFinancialSerializer import (
    LocationFinancialSerializer,
)


class LocationFinancialViewSet(BaseViewSet):
    """
    API endpoint that allows Class Financials to be viewed or edited.
    """

    permission_classes = []
    serializer_class = LocationFinancialSerializer
