from infraohjelmointi_api.models import ProjectType
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectType
