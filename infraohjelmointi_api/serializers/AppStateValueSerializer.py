from infraohjelmointi_api.models import AppStateValueModel
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class AppStateValueSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = AppStateValueModel