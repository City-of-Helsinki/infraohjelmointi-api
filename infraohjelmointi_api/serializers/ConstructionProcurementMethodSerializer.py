from infraohjelmointi_api.models import ConstructionProcurementMethod
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ConstructionProcurementMethodSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ConstructionProcurementMethod


