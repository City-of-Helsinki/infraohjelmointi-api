from infraohjelmointi_api.models import ProjectDistrict
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectDistrictSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectDistrict