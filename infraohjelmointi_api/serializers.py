from .models import (
    ProjectType,
    Project,
    Person,
    ProjectSet,
    ProjectArea,
    BudgetItem,
    Task,
)
from rest_framework import serializers


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]


class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectType
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]


class BudgetItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetItem
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]


class ProjectAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectArea
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]


class ProjectSetSerializer(serializers.ModelSerializer):
    sapProjects = serializers.SerializerMethodField()
    sapNetworks = serializers.SerializerMethodField()

    class Meta:
        model = ProjectSet
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]

    def get_sapProjects(self, obj):
        return obj.sapProjects()

    def get_sapNetworks(self, obj):
        return obj.sapNetworks()


class ProjectGetSerializer(serializers.ModelSerializer):
    projectReadiness = serializers.SerializerMethodField()
    projectSet = ProjectSetSerializer(read_only=True)
    siteId = BudgetItemSerializer(read_only=True)
    area = ProjectAreaSerializer(read_only=True)
    type = ProjectTypeSerializer(read_only=True)
    personPlanning = PersonSerializer(read_only=True)
    personProgramming = PersonSerializer(read_only=True)
    personConstruction = PersonSerializer(read_only=True)

    class Meta:
        model = Project
        # fields = "__all__"
        # depth = 1
        exclude = ["createdDate", "updatedDate"]

    def get_projectReadiness(self, obj):
        return obj.projectReadiness()


class ProjectCreateSerializer(serializers.ModelSerializer):
    projectReadiness = serializers.SerializerMethodField()

    class Meta:
        model = Project
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]

    def get_projectReadiness(self, obj):
        return obj.projectReadiness()


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]
