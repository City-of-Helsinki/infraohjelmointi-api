from infraohjelmointi_api.models import ConstructionPhase
from infraohjelmointi_api.serializers import BaseMeta

from rest_framework import serializers


class ConstructionPhaseSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ConstructionPhase
