from rest_framework import serializers
from infraohjelmointi_api.models import Project
from infraohjelmointi_api.serializers import (
  ConstructionProcurementMethodSerializer
)
  

TASK_TYPE_NAME_CONSTRUCTION_PROJECT_MANAGER = "NAME_CONSTRUCTION_PROJECT_MANAGER"

# NOTE: It's planned that more task types will be added in the future
TASK_TYPES = [
    TASK_TYPE_NAME_CONSTRUCTION_PROJECT_MANAGER,
]

TASK_TYPE_CHOICES = [(task_type, task_type) for task_type in TASK_TYPES]

class ProjectTaskSerializer(serializers.ModelSerializer):
    constructionProcurementMethod = ConstructionProcurementMethodSerializer(read_only=True)
    taskType = serializers.ChoiceField(choices=TASK_TYPE_CHOICES, read_only=True)

    class Meta:
        model = Project
        fields = (
            'id',
            'name',
            'estPlanningStart',
            'estPlanningEnd', 
            'estConstructionStart',
            'estConstructionEnd',
            'costForecast',
            'constructionProcurementMethod',
            'taskType'
        )