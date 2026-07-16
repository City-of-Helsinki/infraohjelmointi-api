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
        if getattr(instance, "is_locked", False):
            raise serializers.ValidationError(
                {"status": "Only entities in DRAFT status can be saved."}
            )

        return attrs


class ProjectProgrammeSectionParentImmutableMixin:
    def validate(self, attrs):
        attrs = super().validate(attrs)

        instance = getattr(self, "instance", None)
        parent = attrs.get("project_programme")
        if instance and parent and parent != instance.project_programme:
            raise serializers.ValidationError(
                {"project_programme": "Section parent project programme cannot be changed."}
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

        if self.instance and ("contentType" in attrs or "objectId" in attrs):
            raise serializers.ValidationError(
                {"detail": "Link target cannot be changed."}
            )

        content_type = attrs.get("contentType", getattr(self.instance, "contentType", None))
        object_id = attrs.get("objectId", getattr(self.instance, "objectId", None))

        if content_type and object_id:
            model_class = content_type.model_class()
            if model_class is not None:
                section_instance = model_class.objects.filter(pk=object_id).first()
                if (
                    section_instance
                    and (
                        getattr(section_instance, "is_locked", False)
                        or (
                            hasattr(section_instance, "status")
                            and section_instance.status != "DRAFT"
                        )
                    )
                ):
                    raise serializers.ValidationError(
                        {
                            "detail": "Links can only be modified for entities in DRAFT status."
                        }
                    )

        return attrs


class ProjectProgrammeBasicInfoGetSerializer(serializers.ModelSerializer):
    BRIEF_ONLY_FIELDS = {"estimatedCosts"}
    COMPLETE_ONLY_FIELDS = {
        "strategyGoals",
        "costClass",
        "projectSize",
        "risks",
        "studyAndPlanningNeeds",
        "planningAndImplementationFeasibility",
        "specialConsiderations",
        "otherConsiderations",
    }

    class Meta:
        model = ProjectProgrammeBasicInfo
        fields = "__all__"

    def get_fields(self):
        fields = super().get_fields()
        programme = getattr(self.instance, "project_programme", None)
        if programme and programme.briefProjectProgramme:
            fields = {
                name: field
                for name, field in fields.items()
                if name not in self.COMPLETE_ONLY_FIELDS
            }
        elif programme:
            fields = {
                name: field
                for name, field in fields.items()
                if name not in self.BRIEF_ONLY_FIELDS
            }
        return fields


class ProjectProgrammeBasicInfoUpdateSerializer(
    ProjectProgrammeSectionParentImmutableMixin,
    ProjectProgrammeDraftOnlyUpdateMixin,
    serializers.ModelSerializer,
):
    BRIEF_ONLY_FIELDS = {"estimatedCosts"}
    COMPLETE_ONLY_FIELDS = {
        "strategyGoals",
        "costClass",
        "projectSize",
        "risks",
        "studyAndPlanningNeeds",
        "planningAndImplementationFeasibility",
        "specialConsiderations",
        "otherConsiderations",
    }
    REQUIRED_IN_ALL_PROGRAMMES = {
        "projectName",
        "district",
        "projectProgrammeCompiler",
        "personsInvolved",
    }
    REQUIRED_IN_BRIEF_PROGRAMMES = {"inspector", "estimatedCosts"}
    REQUIRED_IN_COMPLETE_PROGRAMMES = {
        "summary",
        "strategyGoals",
        "costClass",
        "projectSize",
        "risks",
        "studyAndPlanningNeeds",
        "planningAndImplementationFeasibility",
    }

    class Meta:
        model = ProjectProgrammeBasicInfo
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy"]

    def _get_project_programme(self):
        if self.instance:
            return self.instance.project_programme

        project_programme_id = self.initial_data.get("project_programme")
        if not project_programme_id:
            return None
        return ProjectProgramme.objects.filter(pk=project_programme_id).first()

    def _required_fields_for(self, programme):
        is_brief = programme.briefProjectProgramme
        return self.REQUIRED_IN_ALL_PROGRAMMES | (
            self.REQUIRED_IN_BRIEF_PROGRAMMES
            if is_brief
            else self.REQUIRED_IN_COMPLETE_PROGRAMMES
        )

    def get_fields(self):
        fields = super().get_fields()
        programme = self._get_project_programme()
        if not programme:
            return fields

        is_brief = programme.briefProjectProgramme
        hidden_fields = self.COMPLETE_ONLY_FIELDS if is_brief else self.BRIEF_ONLY_FIELDS
        required_fields = self._required_fields_for(programme)
        for name in hidden_fields:
            fields.pop(name, None)
        if self.instance:
            for name, field in fields.items():
                field.required = name in required_fields
        return fields

    def validate(self, attrs):
        attrs = super().validate(attrs)

        instance = getattr(self, "instance", None)
        if not instance:
            return attrs

        programme = self._get_project_programme()
        if not programme:
            return attrs

        errors = {}
        for name in self._required_fields_for(programme):
            value = attrs.get(name, getattr(instance, name, None))
            if value in (None, ""):
                errors[name] = "This field is required."
        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def to_internal_value(self, data):
        # Prefill from the linked project only on create; on update this must not
        # override values already saved (or silently fail required checks when the
        # project itself has no district).
        if self.instance is not None:
            return super().to_internal_value(data)

        data = data.copy()
        programme = self._get_project_programme()
        project = getattr(programme, "project", None)
        if project is not None:
            data.setdefault("projectName", project.name or "")
            data.setdefault(
                "district",
                project.projectDistrict.name if project.projectDistrict else "",
            )
        return super().to_internal_value(data)

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
    ProjectProgrammeSectionParentImmutableMixin,
    ProjectProgrammeDraftOnlyUpdateMixin,
    serializers.ModelSerializer,
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
    ProjectProgrammeSectionParentImmutableMixin,
    ProjectProgrammeDraftOnlyUpdateMixin,
    serializers.ModelSerializer,
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
    ProjectProgrammeSectionParentImmutableMixin,
    ProjectProgrammeDraftOnlyUpdateMixin,
    serializers.ModelSerializer,
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
    ProjectProgrammeSectionParentImmutableMixin,
    ProjectProgrammeDraftOnlyUpdateMixin,
    serializers.ModelSerializer,
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
    ProjectProgrammeSectionParentImmutableMixin,
    ProjectProgrammeDraftOnlyUpdateMixin,
    serializers.ModelSerializer,
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
        content_type = getattr(self, "_other_attachments_content_type", None)
        if content_type is None:
            content_type = ContentType.objects.get_for_model(ProjectProgrammeOtherAttachments)
            self._other_attachments_content_type = content_type

        links = ProjectProgrammeLink.objects.filter(
            contentType=content_type,
            objectId=instance.id,
        )
        return ProjectProgrammeLinkGetSerializer(links, many=True).data


class ProjectProgrammeOtherAttachmentsUpdateSerializer(
    ProjectProgrammeSectionParentImmutableMixin,
    ProjectProgrammeDraftOnlyUpdateMixin,
    serializers.ModelSerializer,
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


class ProjectProgrammeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectProgramme
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy"]


class ProjectProgrammeUpdateSerializer(
    ProjectProgrammeDraftOnlyUpdateMixin, serializers.ModelSerializer
):
    class Meta:
        model = ProjectProgramme
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy", "status"]

    def validate(self, attrs):
        attrs = super().validate(attrs)

        instance = getattr(self, "instance", None)
        if not instance:
            return attrs

        if "project" in getattr(self, "initial_data", {}):
            raise serializers.ValidationError(
                {"project": "Project programme project cannot be changed."}
            )

        if "project" in attrs and attrs["project"] != instance.project:
            raise serializers.ValidationError(
                {"project": "Project programme project cannot be changed."}
            )

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


class ProjectProgrammeStatusTransitionSerializer(serializers.Serializer):
    to = serializers.ChoiceField(choices=[("DRAFT", "DRAFT"), ("COMPLETE", "COMPLETE")])
