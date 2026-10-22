from rest_framework import serializers


class FinancingPartySerializer(serializers.Serializer):
    id = serializers.CharField()
    value = serializers.CharField()
