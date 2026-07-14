from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from infraohjelmointi_api.models import (
    ProjectProgramme,
    ProjectProgrammeBasicInfo,
    ProjectProgrammeDesignCriteria,
    ProjectProgrammeInteractionAndRelatedProjects,
    ProjectProgrammeLink,
    ProjectProgrammeMaintenanceNeeds,
    ProjectProgrammeOtherAttachments,
    ProjectProgrammeTrafficPlanningCriteria,
    ProjectProgrammeUrbanSpacingPlanningCriteria,
)


class ProjectProgrammeDraftOnlyUpdateMixin:
    def validate(self, attrs):
        attrs = super().validate(attrs)

        instance = getattr(self, "instance", None)
        status = attrs.get("status", getattr(instance, "status", "DRAFT"))
        if status != "DRAFT":
            raise serializers.ValidationError(
                {"status": "Only entities in DRAFT status can be saved."}
            )

        return attrs


class ProjectProgrammeLinkGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProgrammeLink
        fields = "__all__"


class ProjectProgrammeLinkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProgrammeLink
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate"]

    def validate(self, attrs):
        attrs = super().validate(attrs)

        content_type = attrs.get("contentType", getattr(self.instance, "contentType", None))
        object_id = attrs.get("objectId", getattr(self.instance, "objectId", None))

        if not content_type or not object_id:
            return attrs

        model_class = content_type.model_class()
        if model_class is None:
            return attrs

        section_instance = model_class.objects.filter(pk=object_id).first()
        if section_instance and hasattr(section_instance, "status"):
            if section_instance.status != "DRAFT":
                raise serializers.ValidationError(
                    {
                        "status": "Links can only be modified for entities in DRAFT status."
                    }
                )

        return attrs


class ProjectProgrammeBasicInfoGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProgrammeBasicInfo
        fields = "__all__"


class ProjectProgrammeBasicInfoUpdateSerializer(
    ProjectProgrammeDraftOnlyUpdateMixin, serializers.ModelSerializer
):
    class Meta:
        model = ProjectProgrammeBasicInfo
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy"]

    def create(self, validated_data):
        project_programme = validated_data.get("project_programme")
        project = getattr(project_programme, "project", None)

        if project is not None:
            validated_data["projectName"] = project.name or ""
            validated_data["district"] = (
                project.projectDistrict.name if project.projectDistrict else ""
            )

        return super().create(validated_data)


class ProjectProgrammeDesignCriteriaGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProgrammeDesignCriteria
        fields = "__all__"


class ProjectProgrammeDesignCriteriaUpdateSerializer(
    ProjectProgrammeDraftOnlyUpdateMixin, serializers.ModelSerializer
):
    class Meta:
        model = ProjectProgrammeDesignCriteria
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy"]


class ProjectProgrammeTrafficPlanningCriteriaGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProgrammeTrafficPlanningCriteria
        fields = "__all__"


class ProjectProgrammeTrafficPlanningCriteriaUpdateSerializer(
    ProjectProgrammeDraftOnlyUpdateMixin, serializers.ModelSerializer
):
    class Meta:
        model = ProjectProgrammeTrafficPlanningCriteria
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy"]


class ProjectProgrammeUrbanSpacingPlanningCriteriaGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProgrammeUrbanSpacingPlanningCriteria
        fields = "__all__"


class ProjectProgrammeUrbanSpacingPlanningCriteriaUpdateSerializer(
    ProjectProgrammeDraftOnlyUpdateMixin, serializers.ModelSerializer
):
    class Meta:
        model = ProjectProgrammeUrbanSpacingPlanningCriteria
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy"]


class ProjectProgrammeMaintenanceNeedsGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProgrammeMaintenanceNeeds
        fields = "__all__"


class ProjectProgrammeMaintenanceNeedsUpdateSerializer(
    ProjectProgrammeDraftOnlyUpdateMixin, serializers.ModelSerializer
):
    class Meta:
        model = ProjectProgrammeMaintenanceNeeds
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy"]


class ProjectProgrammeInteractionAndRelatedProjectsGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProgrammeInteractionAndRelatedProjects
        fields = "__all__"


class ProjectProgrammeInteractionAndRelatedProjectsUpdateSerializer(
    ProjectProgrammeDraftOnlyUpdateMixin, serializers.ModelSerializer
):
    class Meta:
        model = ProjectProgrammeInteractionAndRelatedProjects
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy"]


class ProjectProgrammeOtherAttachmentsGetSerializer(serializers.ModelSerializer):
    links = serializers.SerializerMethodField()

    class Meta:
        model = ProjectProgrammeOtherAttachments
        fields = "__all__"

    def get_links(self, instance):
        content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)
        links = ProjectProgrammeLink.objects.filter(
            contentType=content_type,
            objectId=instance.id,
        )
        return ProjectProgrammeLinkGetSerializer(links, many=True).data


class ProjectProgrammeOtherAttachmentsUpdateSerializer(
    ProjectProgrammeDraftOnlyUpdateMixin, serializers.ModelSerializer
):
    class Meta:
        model = ProjectProgrammeOtherAttachments
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy"]


class ProjectProgrammeGetSerializer(serializers.ModelSerializer):
    basicInfo = ProjectProgrammeBasicInfoGetSerializer(read_only=True)
    designCriteria = ProjectProgrammeDesignCriteriaGetSerializer(read_only=True)
    trafficPlanningCriteria = ProjectProgrammeTrafficPlanningCriteriaGetSerializer(
        read_only=True
    )
    urbanSpacingPlanningCriteria = (
        ProjectProgrammeUrbanSpacingPlanningCriteriaGetSerializer(read_only=True)
    )
    maintenanceNeeds = ProjectProgrammeMaintenanceNeedsGetSerializer(read_only=True)
    interactionAndRelatedProjects = (
        ProjectProgrammeInteractionAndRelatedProjectsGetSerializer(read_only=True)
    )
    otherAttachments = ProjectProgrammeOtherAttachmentsGetSerializer(read_only=True)

    class Meta:
        model = ProjectProgramme
        fields = "__all__"


class ProjectProgrammeUpdateSerializer(
    ProjectProgrammeDraftOnlyUpdateMixin, serializers.ModelSerializer
):
    class Meta:
        model = ProjectProgramme
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy"]

    def validate(self, attrs):
        attrs = super().validate(attrs)

        instance = getattr(self, "instance", None)
        if not instance:
            return attrs

        current_is_brief = instance.briefProjectProgramme
        new_is_brief = attrs.get("briefProjectProgramme", current_is_brief)

        if current_is_brief is False and new_is_brief is True:
            has_content_entities = any(
                hasattr(instance, relation_name)
                for relation_name in [
                    "designCriteria",
                    "trafficPlanningCriteria",
                    "urbanSpacingPlanningCriteria",
                    "maintenanceNeeds",
                    "interactionAndRelatedProjects",
                    "otherAttachments",
                ]
            )

            if has_content_entities:
                raise serializers.ValidationError(
                    {
                        "briefProjectProgramme": (
                            "Cannot switch from extensive to brief project programme "
                            "after content has been created."
                        )
                    }
                )

        return attrs


class ProjectProgrammeTransitionToCompletedSerializer(serializers.Serializer):
    to = serializers.ChoiceField(choices=[("DRAFT", "DRAFT"), ("COMPLETE", "COMPLETE")])
