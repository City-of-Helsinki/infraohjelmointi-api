from infraohjelmointi_api.models import ResponsibleZone
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class ProjectResponsibleZoneSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ResponsibleZone
