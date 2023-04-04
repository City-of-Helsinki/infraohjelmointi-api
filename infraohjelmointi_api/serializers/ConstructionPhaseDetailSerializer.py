from infraohjelmointi_api.models import ConstructionPhaseDetail
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ConstructionPhaseDetailSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ConstructionPhaseDetail
