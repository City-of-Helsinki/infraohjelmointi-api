from infraohjelmointi_api.models import ProjectPhase
from infraohjelmointi_api.serializers import BaseMeta

from rest_framework import serializers


class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectPhase
