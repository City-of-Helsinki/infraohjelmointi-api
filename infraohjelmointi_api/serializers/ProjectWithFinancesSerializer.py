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
        forcedToFrame = self.context.get("forcedToFrame", False)
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
        queryset = project.finances_filtered
        allFinances = ProjectFinancialSerializer(queryset, many=True).data
        serializedFinances = {
            "year": year,
            "budgetProposalCurrentYearPlus0": "0.00",
            "budgetProposalCurrentYearPlus1": "0.00",
            "budgetProposalCurrentYearPlus2": "0.00",
            "preliminaryCurrentYearPlus3": "0.00",
            "preliminaryCurrentYearPlus4": "0.00",
            "preliminaryCurrentYearPlus5": "0.00",
            "preliminaryCurrentYearPlus6": "0.00",
            "preliminaryCurrentYearPlus7": "0.00",
            "preliminaryCurrentYearPlus8": "0.00",
            "preliminaryCurrentYearPlus9": "0.00",
            "preliminaryCurrentYearPlus10": "0.00",
        }

        for finance in allFinances:
            serializedFinances[yearToFieldMapping[finance["year"]]] = finance["value"]
            # pop out already mapped keys
            yearToFieldMapping.pop(finance["year"])

        return serializedFinances

    class Meta(BaseMeta):
        model = Project
