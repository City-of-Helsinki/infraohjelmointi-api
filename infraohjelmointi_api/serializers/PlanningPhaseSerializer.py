from infraohjelmointi_api.models import PlanningPhase
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class PlanningPhaseSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = PlanningPhase
