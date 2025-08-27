from rest_framework import serializers
from infraohjelmointi_api.models import ProjectProgrammer
from infraohjelmointi_api.serializers import BaseMeta


class ProjectProgrammerSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectProgrammer
