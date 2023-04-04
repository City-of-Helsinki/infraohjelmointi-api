from infraohjelmointi_api.models import Project, ProjectGroup
from infraohjelmointi_api.serializers import (
    BaseMeta,
    DynamicFieldsModelSerializer,
    ProjectHashtagSerializer,
)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from overrides import override
from rest_framework.exceptions import ValidationError

from django.shortcuts import get_object_or_404


class ProjectGroupSerializer(DynamicFieldsModelSerializer):

    projects = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False, allow_empty=True
    )

    def validate_projects(self, projectIds):
        """
        Check that project doesn't already belong to a group
        """

        if projectIds is not None and len(projectIds) > 0:
            for projectId in projectIds:
                project = get_object_or_404(Project, pk=projectId)
                if project.projectGroup is not None:
                    raise ValidationError(
                        detail="Project: {} with id: {} already belongs to the group: {} with id: {}".format(
                            project.name,
                            projectId,
                            project.projectGroup.name,
                            project.projectGroup_id,
                        ),
                        code="project_in_group",
                    )
        return projectIds

    class Meta(BaseMeta):
        model = ProjectGroup
        validators = [
            UniqueTogetherValidator(
                queryset=ProjectGroup.objects.all(),
                fields=["name", "classRelation", "districtRelation"],
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
