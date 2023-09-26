from infraohjelmointi_api.models import TaskStatus
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = TaskStatus
