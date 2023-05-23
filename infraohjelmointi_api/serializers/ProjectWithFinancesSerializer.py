from datetime import date
from infraohjelmointi_api.models import Project
from infraohjelmointi_api.serializers import BaseMeta
from infraohjelmointi_api.serializers.ProjectFinancialSerializer import (
    ProjectFinancialSerializer,
)
from infraohjelmointi_api.services import ProjectFinancialService
from rest_framework import serializers


class ProjectWithFinancesSerializer(serializers.ModelSerializer):
    finances = serializers.SerializerMethodField()

    def get_finances(self, project):
        """
        A function used to get financial fields of a project using context passed to the serializer.
        If no year is passed to the serializer using either the project id or finance_year as key
        the current year is used as the default.
        """
        year = self.context.get(
            str(project.id), self.context.get("finance_year", date.today().year)
        )
        if year is None:
            year = date.today().year
        queryset, _ = ProjectFinancialService.get_or_create(
            project_id=project.id, year=year
        )

        return ProjectFinancialSerializer(queryset, many=False).data

    class Meta(BaseMeta):
        model = Project
