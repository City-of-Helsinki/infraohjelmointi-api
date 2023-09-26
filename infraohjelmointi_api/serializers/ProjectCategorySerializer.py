from infraohjelmointi_api.models import ProjectCategory
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectCategorySerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectCategory
