from .models import ProjectType, Project
from rest_framework import serializers


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

        lookup_field = 'type'
        extra_kwargs = {
            'url': {'lookup_field': 'type'}
        }


class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectType
        fields = '__all__'