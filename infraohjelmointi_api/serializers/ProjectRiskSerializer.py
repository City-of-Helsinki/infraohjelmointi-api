from infraohjelmointi_api.models import ProjectRisk
from infraohjelmointi_api.serializers import BaseMeta

from rest_framework import serializers


class ProjectRiskSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectRisk
