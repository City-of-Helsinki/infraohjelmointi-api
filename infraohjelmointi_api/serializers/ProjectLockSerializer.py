from rest_framework import serializers
from ..models import ProjectLock
from .BaseMeta import BaseMeta


class ProjectLockSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectLock
