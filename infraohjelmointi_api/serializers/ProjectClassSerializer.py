from infraohjelmointi_api.models import ProjectClass
from infraohjelmointi_api.serializers import BaseMeta, FinancialSumSerializer
from rest_framework import serializers


class ProjectClassSerializer(FinancialSumSerializer, serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectClass
