from rest_framework import serializers
from infraohjelmointi_api.models import ConstructionHandover


class ConstructionHandoverUpdateSerializer(serializers.ModelSerializer):
    constructionStart = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    constructionEnd = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )

    class Meta:
        fields = "__all__"
        read_only_fields = ["createdDate", "updatedDate", "createdBy", "updatedBy", "status"]
        model = ConstructionHandover