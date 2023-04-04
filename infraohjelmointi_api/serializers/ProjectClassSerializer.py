from infraohjelmointi_api.models import ProjectClass
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectClassSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectClass
