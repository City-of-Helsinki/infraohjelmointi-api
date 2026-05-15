from rest_framework import serializers
from infraohjelmointi_api.models import ConstructionHandover
from infraohjelmointi_api.serializers import (
  ConstructionProcurementMethodSerializer,
  PersonSerializer,
  ProjectProgrammerSerializer
)

class ConstructionHandoverGetSerializer(serializers.ModelSerializer):
    personPlanning = PersonSerializer(read_only=True)
    personFinancing = ProjectProgrammerSerializer(read_only=True)
    constructionProcurementMethod = ConstructionProcurementMethodSerializer(read_only=True)

    class Meta:
        model = ConstructionHandover
        fields = "__all__"