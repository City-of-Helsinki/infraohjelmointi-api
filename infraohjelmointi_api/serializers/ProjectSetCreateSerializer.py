from infraohjelmointi_api.models import ProjectSet
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectSetCreateSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectSet
