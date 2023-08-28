from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.BudgetItemSerializer import BudgetItemSerializer


class BudgetItemViewSet(BaseViewSet):
    """
    API endpoint that allows Budgets to be viewed or edited.
    """

    permission_classes = []
    serializer_class = BudgetItemSerializer
