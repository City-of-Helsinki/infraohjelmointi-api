from infraohjelmointi_api.models import Project, ProjectGroup
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.DynamicFieldsModelSerializer import (
    DynamicFieldsModelSerializer,
)
from infraohjelmointi_api.serializers.FinancialSumSerializer import (
    FinancialSumSerializer,
)
from infraohjelmointi_api.validators.ProjectGroupValidators.ProjectsFieldValidator import (
    ProjectsFieldValidator,
)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from overrides import override
from rest_framework.exceptions import ValidationError

from django.shortcuts import get_object_or_404


class ProjectGroupSerializer(DynamicFieldsModelSerializer, FinancialSumSerializer):
    projects = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True,
        validators=[ProjectsFieldValidator()],
    )

    class Meta(BaseMeta):
        model = ProjectGroup
        validators = [
            UniqueTogetherValidator(
                queryset=ProjectGroup.objects.all(),
                fields=["name", "classRelation", "locationRelation"],
            ),
        ]

    @override
    def create(self, validated_data):
        projectIds = validated_data.pop("projects", None)
        projectGroup = self.Meta.model.objects.create(**validated_data)
        if projectIds is not None and len(projectIds) > 0:
            for projectId in projectIds:
                project = get_object_or_404(Project, pk=projectId)
                project.projectGroup = projectGroup
                project.save()

        return projectGroup
