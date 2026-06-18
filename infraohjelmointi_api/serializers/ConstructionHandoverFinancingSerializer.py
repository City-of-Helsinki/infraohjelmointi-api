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

    def _resolve_handover(self, attrs):
        handover_id = attrs.get("handover")
        if handover_id is None:
            return

        try:
            attrs["handover"] = ConstructionHandover.objects.get(id=handover_id)
        except ConstructionHandover.DoesNotExist:
            raise serializers.ValidationError({"handover": "Invalid handover id."})

    def _effective_value(self, attrs, field):
        if field in attrs:
            return attrs[field]
        if self.instance:
            return getattr(self.instance, field, None)
        return None

    def _effective_financing_party(self, attrs):
        financing_party = attrs.get("financingParty")
        if financing_party is None and self.instance:
            financing_party = self.instance.financingParty
        return financing_party

    def _effective_budget_item(self, attrs):
        if "budgetItem" in attrs:
            return attrs["budgetItem"]
        if self.instance:
            return self.instance.budgetItem
        return None

    def _validate_kymp(self, attrs):
        budget_item = self._effective_budget_item(attrs)
        if budget_item is None:
            raise serializers.ValidationError(
                {"budgetItemId": "Budget item is required for KYMP financing."}
            )
        if not self._effective_value(attrs, "budget"):
            raise serializers.ValidationError(
                {"budget": "Budget is required for KYMP financing."}
            )
        if not self._effective_value(attrs, "projectNumber"):
            raise serializers.ValidationError(
                {"projectNumber": "Project number is required for KYMP financing."}
            )

    def _validate_other(self, attrs):
        if not self._effective_value(attrs, "description"):
            raise serializers.ValidationError(
                {"description": "Description is required when financing party is OTHER."}
            )
        if not self._effective_value(attrs, "budget"):
            raise serializers.ValidationError(
                {"budget": "Budget is required for OTHER financing."}
            )

    def _validate_other_financing_party(self, attrs):
        if not self._effective_value(attrs, "budget"):
            raise serializers.ValidationError({"budget": "Budget is required."})
        if (
            "financingParty" in attrs
            and "budgetItem" not in attrs
            and self.instance
            and self.instance.budgetItem
        ):
            attrs["budgetItem"] = None

    def validate(self, attrs):
        attrs = super().validate(attrs)

        self._resolve_handover(attrs)

        financing_party = self._effective_financing_party(attrs)
        if financing_party == "KYMP":
            self._validate_kymp(attrs)
        elif financing_party == "OTHER":
            self._validate_other(attrs)
        elif financing_party is not None:
            self._validate_other_financing_party(attrs)

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

        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("project", None)
        return super().update(instance, validated_data)
