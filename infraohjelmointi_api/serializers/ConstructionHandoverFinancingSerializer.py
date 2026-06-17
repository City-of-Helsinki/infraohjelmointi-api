from rest_framework import serializers
from rest_framework.settings import api_settings

from infraohjelmointi_api.models import (
    ConstructionHandover,
    ConstructionHandoverFinancing,
    ProjectTypeQualifier,
)
from infraohjelmointi_api.serializers.ProjectTypeQualifierSerializer import (
    ProjectTypeQualifierSerializer,
)


class ConstructionHandoverFinancingSerializer(serializers.ModelSerializer):
    budgetItem = ProjectTypeQualifierSerializer(read_only=True)
    handover = serializers.UUIDField(required=False, allow_null=True)
    budgetItemId = serializers.PrimaryKeyRelatedField(
        queryset=ProjectTypeQualifier.objects.all(),
        source="budgetItem",
        write_only=True,
        required=False,
        allow_null=True,
    )
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
        if financing_party is None and self.instance:
            financing_party = self.instance.financingParty

        # Helper: get effective value from attrs or instance (for partial updates)
        def effective(field):
            if field in attrs:
                return attrs[field]
            if self.instance:
                return getattr(self.instance, field, None)
            return None

        if financing_party == "KYMP":
            # budgetItem required: check attrs first, then instance
            if "budgetItem" in attrs:
                budget_item = attrs["budgetItem"]
            elif self.instance:
                budget_item = self.instance.budgetItem
            else:
                budget_item = None
            if budget_item is None:
                raise serializers.ValidationError(
                    {"budgetItemId": "Budget item is required for KYMP financing."}
                )
            if not effective("budget"):
                raise serializers.ValidationError(
                    {"budget": "Budget is required for KYMP financing."}
                )
            if not effective("projectNumber"):
                raise serializers.ValidationError(
                    {"projectNumber": "Project number is required for KYMP financing."}
                )
        elif financing_party == "OTHER":
            if not effective("description"):
                raise serializers.ValidationError(
                    {"description": "Description is required when financing party is OTHER."}
                )
            if not effective("budget"):
                raise serializers.ValidationError(
                    {"budget": "Budget is required for OTHER financing."}
                )
        elif financing_party is not None:
            # All other parties: only budget is required; budgetItemId is not used
            if not effective("budget"):
                raise serializers.ValidationError({"budget": "Budget is required."})
            # If changing to a non-KYMP party, clear any existing budgetItem
            if "financingParty" in attrs and "budgetItem" not in attrs and self.instance and self.instance.budgetItem:
                attrs["budgetItem"] = None

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
