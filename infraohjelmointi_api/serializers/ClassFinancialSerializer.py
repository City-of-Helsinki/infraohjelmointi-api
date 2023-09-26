from infraohjelmointi_api.models import ClassFinancial, ProjectClass
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.validators.ClassFinancialValidators import (
    ClassRelationFieldValidator,
)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator


class ClassFinancialSerializer(serializers.ModelSerializer):
    classRelation = serializers.PrimaryKeyRelatedField(
        many=False,
        validators=[ClassRelationFieldValidator()],
        queryset=ProjectClass.objects.all(),
    )

    class Meta(BaseMeta):
        model = ClassFinancial
        exclude = ["createdDate", "updatedDate", "id"]
        validators = [
            UniqueTogetherValidator(
                queryset=ClassFinancial.objects.all(),
                fields=["year", "classRelation"],
            ),
        ]
