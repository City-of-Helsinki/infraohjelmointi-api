from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ClassFinancialSerializer import (
    ClassFinancialSerializer,
)


class ClassFinancialViewSet(BaseViewSet):
    """
    API endpoint that allows Class Financials to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ClassFinancialSerializer
