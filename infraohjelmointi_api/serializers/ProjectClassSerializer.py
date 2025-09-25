from infraohjelmointi_api.models import ProjectClass
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.FinancialSumSerializer import (
    FinancialSumSerializer,
)
from infraohjelmointi_api.serializers.ProjectProgrammerSerializer import (
    ProjectProgrammerSerializer,
)


class ProjectClassSerializer(FinancialSumSerializer):
    defaultProgrammer = ProjectProgrammerSerializer(read_only=True)

    class Meta(BaseMeta):
        model = ProjectClass
