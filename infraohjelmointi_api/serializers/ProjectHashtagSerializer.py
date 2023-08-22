from infraohjelmointi_api.models import ProjectHashTag
from infraohjelmointi_api.serializers import BaseMeta, DynamicFieldsModelSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class ProjectHashtagSerializer(DynamicFieldsModelSerializer):
    usageCount = serializers.SerializerMethodField(read_only=True)
    value = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=ProjectHashTag.objects.all(),
                message=("HashTag with this name already exists"),
            )
        ]
    )

    class Meta(BaseMeta):
        exclude = ["updatedDate"]
        model = ProjectHashTag

    def get_usageCount(self, hashTag: ProjectHashTag):
        return hashTag.relatedProject.count()
