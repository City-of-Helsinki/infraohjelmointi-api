from infraohjelmointi_api.models import ProjectArea
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectAreaSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectArea
        exclude = ["createdDate", "updatedDate", "location"]
