from infraohjelmointi_api.models import ProjectHashTag
from infraohjelmointi_api.serializers import BaseMeta, DynamicFieldsModelSerializer
from rest_framework import serializers


class ProjectHashtagSerializer(DynamicFieldsModelSerializer):
    usageCount = serializers.SerializerMethodField(read_only=True)

    class Meta(BaseMeta):
        exclude = ["updatedDate"]
        model = ProjectHashTag

    def get_usageCount(self, hashTag: ProjectHashTag):
        return hashTag.relatedProject.count()
