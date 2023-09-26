from infraohjelmointi_api.models import ProjectQualityLevel
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectQualityLevelSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectQualityLevel
