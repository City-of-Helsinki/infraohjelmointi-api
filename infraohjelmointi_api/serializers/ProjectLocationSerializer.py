from infraohjelmointi_api.models import ProjectLocation
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.FinancialSumSerializer import (
    FinancialSumSerializer,
)
from rest_framework import serializers


class ProjectLocationSerializer(FinancialSumSerializer):
    class Meta(BaseMeta):
        model = ProjectLocation
