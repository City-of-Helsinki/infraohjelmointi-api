from infraohjelmointi_api.models import ProjectFinancial
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.validators.ProjectFinancialValidators import (
    LockedFieldsValidator,
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
                fields=["year", "project"],
            ),
            LockedFieldsValidator(),
        ]

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop("project")
        return rep

    @override
    def update(self, instance, validated_data):
        # Check if project is locked and any locked fields are not being updated
        if hasattr(instance.project, "lock"):
            lockedFields = [
                "budgetProposalCurrentYearPlus0",
                "budgetProposalCurrentYearPlus1",
                "budgetProposalCurrentYearPlus2",
                "preliminaryCurrentYearPlus3",
                "preliminaryCurrentYearPlus4",
                "preliminaryCurrentYearPlus5",
                "preliminaryCurrentYearPlus6",
                "preliminaryCurrentYearPlus7",
                "preliminaryCurrentYearPlus8",
                "preliminaryCurrentYearPlus9",
                "preliminaryCurrentYearPlus10",
            ]
            for field in lockedFields:
                if validated_data.get(field, None) is not None:
                    raise serializers.ValidationError(
                        "The field {} cannot be modified when the project is locked".format(
                            field
                        )
                    )

        return super(ProjectFinancialSerializer, self).update(instance, validated_data)
