from infraohjelmointi_api.models import ProjectLocation
from infraohjelmointi_api.serializers import BaseMeta, FinancialSumSerializer
from rest_framework import serializers


class ProjectLocationSerializer(FinancialSumSerializer, serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectLocation
