from infraohjelmointi_api.models import ProjectPhaseDetail
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.ProjectPhaseSerializer import ProjectPhaseSerializer
from rest_framework import serializers


class ProjectPhaseDetailSerializer(serializers.ModelSerializer):
    projectPhase = ProjectPhaseSerializer(read_only=True)

    class Meta(BaseMeta):
        model = ProjectPhaseDetail
