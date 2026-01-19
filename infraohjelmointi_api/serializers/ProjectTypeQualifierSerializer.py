from infraohjelmointi_api.models import ProjectTypeQualifier
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectTypeQualifierSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectTypeQualifier
