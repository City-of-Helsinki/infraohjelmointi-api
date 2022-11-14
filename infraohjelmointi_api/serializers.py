from infraohjelmointi_api.models import ProjectType, Project
from rest_framework import serializers


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'HKRprojectID', 'type', 'created_date', 'updated_date']

        lookup_field = 'type'
        extra_kwargs = {
            'url': {'lookup_field': 'type'}
        }


class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectType
        fields = ['id', 'value']