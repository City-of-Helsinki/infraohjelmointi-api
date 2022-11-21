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


class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectType
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]


class ProjectAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectArea
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]


class BudgetItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BudgetItem
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        # fields = "__all__"
        exclude = ["createdDate", "updatedDate"]
