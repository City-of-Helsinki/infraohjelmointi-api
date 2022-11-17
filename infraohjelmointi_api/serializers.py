from .models import ProjectType, Project, Person, ProjectSet
from rest_framework import serializers


class ProjectSerializer(serializers.ModelSerializer):
    projectReadiness = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = "__all__"

        lookup_field = "type"
        extra_kwargs = {"url": {"lookup_field": "type"}}

    def get_projectReadiness(self, obj):
        return obj.projectReadiness()


class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectType
        fields = "__all__"


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = "__all__"


class ProjectSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSet
        fields = "__all__"
