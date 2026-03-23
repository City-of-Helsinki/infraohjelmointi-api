from infraohjelmointi_api.models import StaraProcurementReason
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class StaraProcurementReasonSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = StaraProcurementReason


