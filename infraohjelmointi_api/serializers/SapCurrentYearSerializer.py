from infraohjelmointi_api.models import SapCurrentYear
from rest_framework import serializers


class SapCurrentYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = SapCurrentYear
        fields = (
            "id",
            "year",
            "sap_id",
            "project_task_costs",
            "project_task_commitments",
            "production_task_costs",
            "production_task_commitments",
            "group_combined_commitments",
            "group_combined_costs",
            "project_id",
            "project_group_id",
        )