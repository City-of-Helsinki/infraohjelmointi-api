from infraohjelmointi_api.models import ProjectClass
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.FinancialSumSerializer import (
    FinancialSumSerializer,
)
from rest_framework import serializers


class ProjectClassSerializer(FinancialSumSerializer):
    class Meta(BaseMeta):
        model = ProjectClass
