from infraohjelmointi_api.models import BudgetOverrunReason
from infraohjelmointi_api.serializers import BaseMeta

from rest_framework import serializers


class BudgetOverrunReasonSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = BudgetOverrunReason