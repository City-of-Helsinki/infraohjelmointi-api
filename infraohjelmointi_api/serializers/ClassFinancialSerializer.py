from infraohjelmointi_api.models import ClassFinancial
from infraohjelmointi_api.serializers import BaseMeta

from rest_framework import serializers
from overrides import override
from rest_framework.validators import UniqueTogetherValidator


class ClassFinancialSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ClassFinancial
        exclude = ["createdDate", "updatedDate", "id"]
        validators = [
            UniqueTogetherValidator(
                queryset=ClassFinancial.objects.all(),
                fields=["year", "classRelation"],
            ),
        ]
