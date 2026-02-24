from .CachedLookupViewSet import CachedLookupViewSet
from infraohjelmointi_api.serializers.BudgetOverrunReasonSerializer import BudgetOverrunReasonSerializer


class BudgetOverrunReasonViewSet(CachedLookupViewSet):
    """
    API endpoint that allows budget overrun reasons to be viewed or edited.
    """

    serializer_class = BudgetOverrunReasonSerializer