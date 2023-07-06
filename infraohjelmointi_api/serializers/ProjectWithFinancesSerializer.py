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
        year = int(year)
        yearToFieldMapping = (
            ProjectFinancialService.get_year_to_financial_field_names_mapping(
                start_year=year
            )
        )
        queryset = ProjectFinancialService.find_by_project_id_and_year_range(
            project_id=project.id, year_range=range(year, year + 11)
        )
        allFinances = ProjectFinancialSerializer(queryset, many=True).data
        serializedFinances = {"year": year}
        for finance in allFinances:
            serializedFinances[yearToFieldMapping[finance["year"]]] = finance["value"]
            # pop out already mapped keys
            yearToFieldMapping.pop(finance["year"])
        # remaining year keys which had no data in DB
        for yearKey in yearToFieldMapping.keys():
            serializedFinances[yearToFieldMapping[yearKey]] = "0.00"

        return serializedFinances

    class Meta(BaseMeta):
        model = Project
