from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.BudgetOverrunReasonSerializer import BudgetOverrunReasonSerializer
from .CachedLookupViewSet import CachedLookupViewSet


class BudgetOverrunReasonViewSet(CachedLookupViewSet):
    """
    API endpoint that allows budget overrun reasons to be viewed or edited.
    """

    serializer_class = BudgetOverrunReasonSerializer

