from infraohjelmointi_api.models import ProjectFinancial
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.validators.ProjectFinancialValidators import (
    LockedFieldsValidator,
)
from infraohjelmointi_api.services.ProjectFinancialService import (
    ProjectFinancialService,
)
from rest_framework import serializers
from overrides import override
from rest_framework.validators import UniqueTogetherValidator


class ProjectFinancialSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectFinancial
        exclude = ["createdDate", "updatedDate", "id"]
        validators = [
            UniqueTogetherValidator(
                queryset=ProjectFinancial.objects.all(),
                fields=["year", "project", "forFrameView"],
            ),
            LockedFieldsValidator(),
        ]

    @override
    def create(self, validated_data):
        # Check if a non frame view project financial is created and the related frameview financial does not exist
        if validated_data.get("forframeView", False) == False:
            if not ProjectFinancialService.instance_exists(
                project_id=validated_data.get("project").id,
                year=validated_data.get("year"),
                for_frame_view=True,
            ):
                ProjectFinancialService.create(
                    project_id=validated_data.get("project").id,
                    year=validated_data.get("year"),
                    for_frame_view=True,
                    value=validated_data.get("value", 0),
                )

        projectFinancialObject = super(ProjectFinancialSerializer, self).create(
            validated_data
        )

        return projectFinancialObject

    @override
    def update(self, instance: ProjectFinancial, validated_data):
        # Check if a non frame view project financial is updated and the related frameview financial does not exist
        if instance.forFrameView == False:
            if not ProjectFinancialService.instance_exists(
                project_id=instance.project.id,
                year=instance.year,
                for_frame_view=True,
            ):
                ProjectFinancialService.create(
                    project_id=instance.project.id,
                    year=instance.year,
                    for_frame_view=True,
                    value=validated_data.get("value", 0),
                )
        return super(ProjectFinancialSerializer, self).update(instance, validated_data)

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop("project")
        return rep
