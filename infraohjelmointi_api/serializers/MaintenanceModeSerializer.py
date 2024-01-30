from infraohjelmointi_api.models import MaintenanceMode
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class MaintenanceModeSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = MaintenanceMode