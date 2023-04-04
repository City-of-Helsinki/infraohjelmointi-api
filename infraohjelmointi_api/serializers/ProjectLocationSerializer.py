from infraohjelmointi_api.models import ProjectLocation
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectLocationSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectLocation
