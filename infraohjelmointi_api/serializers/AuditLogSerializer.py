from infraohjelmointi_api.models import AuditLog
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = AuditLog