from infraohjelmointi_api.models import BudgetItem
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class BudgetItemSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = BudgetItem
