from rest_framework import serializers
from infraohjelmointi_api.models import ConstructionHandover
from infraohjelmointi_api.serializers.ConstructionHandoverFinancingSerializer import ConstructionHandoverFinancingSerializer
from infraohjelmointi_api.serializers import (
  ConstructionProcurementMethodSerializer,
  PersonSerializer,
  ProjectProgrammerSerializer,
  StaraProcurementReasonSerializer
)

class ConstructionHandoverGetSerializer(serializers.ModelSerializer):
    personPlanning = PersonSerializer(read_only=True)
    personFinancing = ProjectProgrammerSerializer(read_only=True)
    constructionProcurementMethod = ConstructionProcurementMethodSerializer(read_only=True)
    staraProcurementReason = StaraProcurementReasonSerializer(read_only=True)
    constructionProjectManager = PersonSerializer(read_only=True)
    constructionHandoverFinancing = ConstructionHandoverFinancingSerializer(
        many=True, read_only=True, source='financing'
    )

    class Meta:
        model = ConstructionHandover
        fields = "__all__"