from rest_framework import serializers
from infraohjelmointi_api.models import ConstructionHandover
from infraohjelmointi_api.serializers.ConstructionHandoverFinancingSerializer import ConstructionHandoverFinancingSerializer
from infraohjelmointi_api.serializers.ConstructionHandoverAttachmentSerializer import ConstructionHandoverAttachmentSerializer
from infraohjelmointi_api.serializers import (
  ConstructionProcurementMethodSerializer,
  PersonSerializer,
  ProjectProgrammerSerializer
)

class ConstructionHandoverGetSerializer(serializers.ModelSerializer):
    personPlanning = PersonSerializer(read_only=True)
    personFinancing = ProjectProgrammerSerializer(read_only=True)
    constructionProcurementMethod = ConstructionProcurementMethodSerializer(read_only=True)
    constructionProjectManager = PersonSerializer(read_only=True)
    constructionHandoverFinancing = ConstructionHandoverFinancingSerializer(
        many=True, read_only=True, source='financing'
    )
    # IO-857: embedded so the "Liitteet ja linkit" section (IO-856) can render the
    # existing attachments without a second request.
    attachments = ConstructionHandoverAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = ConstructionHandover
        fields = "__all__"