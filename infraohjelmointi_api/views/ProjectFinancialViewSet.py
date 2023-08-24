from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectFinancialSerializer import (
    ProjectFinancialSerializer,
)
from infraohjelmointi_api.models import ProjectFinancial
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


class ProjectFinancialViewSet(BaseViewSet):
    """
    API endpoint that allows Project Finances to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectFinancialSerializer

    @action(
        methods=["get"],
        detail=False,
        url_path=r"(?P<project>[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12})/(?P<year>[0-9]{4})",
    )
    def get_finances_by_year(self, request, project, year):
        """
        Custom action to get finances of a project for an year.

            URL Parameters
            ----------

            project_id : UUID string
            year : Int

            Usage
            ----------

            project-financials/<project_id>/<year>

            Returns
            -------

            JSON
                ProjectFinancial instance for the given year and project id
        """
        queryFilter = {"project": project, "year": year}
        finance_object = get_object_or_404(ProjectFinancial, **queryFilter)
        return Response(ProjectFinancialSerializer(finance_object).data)
