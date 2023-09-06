from infraohjelmointi_api.models import LocationFinancial, ProjectLocation
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.validators.LocationFinancialValidators import (
    LocationRelationFieldValidator,
)
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator


class LocationFinancialSerializer(serializers.ModelSerializer):
    classRelation = serializers.PrimaryKeyRelatedField(
        many=False,
        validators=[LocationRelationFieldValidator()],
        queryset=LocationFinancial.objects.all(),
    )

    class Meta(BaseMeta):
        model = LocationFinancial
        exclude = ["createdDate", "updatedDate", "id"]
        validators = [
            UniqueTogetherValidator(
                queryset=LocationFinancial.objects.all(),
                fields=["year", "locationRelation"],
            ),
        ]
