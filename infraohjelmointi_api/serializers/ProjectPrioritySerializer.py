from infraohjelmointi_api.models import ProjectPriority
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectPrioritySerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectPriority
