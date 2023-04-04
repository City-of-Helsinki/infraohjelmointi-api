from infraohjelmointi_api.models import Task
from infraohjelmointi_api.serializers import BaseMeta
from rest_framework import serializers


class TaskSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = Task
