from rest_framework import serializers
from infraohjelmointi_api.models import ConstructionHandover


class ConstructionHandoverCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConstructionHandover
        fields = "__all__"