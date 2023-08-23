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
                fields=["year", "project", "forFrameView"],
            ),
            LockedFieldsValidator(),
        ]

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop("project")
        return rep
