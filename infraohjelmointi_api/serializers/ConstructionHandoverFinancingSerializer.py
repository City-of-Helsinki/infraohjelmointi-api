from rest_framework import serializers
from rest_framework.settings import api_settings

from infraohjelmointi_api.models import ConstructionHandover, ConstructionHandoverFinancing
from infraohjelmointi_api.serializers.ProjectTypeQualifierSerializer import (
    ProjectTypeQualifierSerializer,
)


class ConstructionHandoverFinancingSerializer(serializers.ModelSerializer):
    budgetItem = ProjectTypeQualifierSerializer(read_only=True)
    handover = serializers.UUIDField(required=False, allow_null=True)
    budgetItemId = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    project = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = ConstructionHandoverFinancing
        fields = [
            "id",
            "handover",
            "project",
            "financingParty",
            "description",
            "budgetItem",
            "budgetItemId",
            "projectNumber",
            "budget",
            "createdDate",
            "updatedDate",
        ]
        read_only_fields = ["id", "createdDate", "updatedDate"]

    @staticmethod
    def _locked_handover_error():
        return serializers.ValidationError(
            {
                api_settings.NON_FIELD_ERRORS_KEY: [
                    "Only construction handovers in DRAFT status can be edited."
                ]
            }
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["handover"] = str(instance.handover_id) if instance.handover_id else None
        return data

    def validate(self, attrs):
        attrs = super().validate(attrs)

        handover_id = attrs.get("handover")
        if handover_id is not None:
            try:
                attrs["handover"] = ConstructionHandover.objects.get(id=handover_id)
            except ConstructionHandover.DoesNotExist:
                raise serializers.ValidationError({"handover": "Invalid handover id."})

        financing_party = attrs.get("financingParty")
        if financing_party == "OTHER" and not attrs.get("description"):
            raise serializers.ValidationError({
                "description": "Description is required when financing party is OTHER.",
            })

        if "budgetItemId" in attrs:
            budget_item_id = attrs.pop("budgetItemId")
            if budget_item_id is None:
                attrs["budgetItem"] = None
            else:
                from infraohjelmointi_api.models import ProjectTypeQualifier

                try:
                    attrs["budgetItem"] = ProjectTypeQualifier.objects.get(id=budget_item_id)
                except ProjectTypeQualifier.DoesNotExist:
                    raise serializers.ValidationError({"budgetItemId": "Invalid project type qualifier id."})

        return attrs

    def create(self, validated_data):
        project_id = validated_data.pop("project", None)
        handover = validated_data.get("handover")

        if handover is None and project_id is None:
            raise serializers.ValidationError({
                "handover": "Either handover or project is required.",
            })

        if handover is None and project_id is not None:
            handover = (
                ConstructionHandover.objects.filter(project_id=project_id)
                .exclude(status="MOVED_TO_CONSTRUCTION_PREPARATION")
                .order_by("-createdDate")
                .first()
            )
            if handover is None:
                raise serializers.ValidationError({
                    "project": "No active construction handover found for this project.",
                })
            validated_data["handover"] = handover

        if handover and handover.is_locked:
            raise self._locked_handover_error()

        return super().create(validated_data)

    def update(self, instance, validated_data):
        if instance.handover.is_locked:
            raise self._locked_handover_error()

        validated_data.pop("project", None)
        return super().update(instance, validated_data)
