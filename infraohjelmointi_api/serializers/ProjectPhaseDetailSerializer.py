from infraohjelmointi_api.models import ProjectPhaseDetail
from rest_framework import serializers


class ProjectPhaseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhaseDetail
        fields = "__all__"
