from datetime import date
from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectLocationSerializer import (
    ProjectLocationSerializer,
)
from infraohjelmointi_api.services import ProjectLocationService
from overrides import override
from rest_framework.response import Response
from rest_framework.decorators import action


class ProjectLocationViewSet(BaseViewSet):
    """
    API endpoint that allows Project Locations to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectLocationSerializer

    @override
    def list(self, request, *args, **kwargs):
        """
        Overriden list action to get a list of ProjectLocation

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Locations with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-locations/?year=<year>

            Returns
            -------

            JSON
                List of ProjectLocation instances with financial sums for projects under each location
        """
        year = request.query_params.get("year", date.today().year)
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True, context={"finance_year": year})

        return Response(serializer.data)

    @override
    def get_queryset(self):
        """Default is programmer view"""
        return ProjectLocationService.list_all()

    @action(methods=["get"], detail=False, url_path=r"coordinator")
    def list_for_coordinator(self, request):
        """
        Overriden list action to get a list of coordinator ProjectLocations

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Locations with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-locations/coordinator/?year=<year>

            Returns
            -------

            JSON
                List of ProjectLocation instances with financial sums for projects under each location
        """
        year = request.query_params.get("year", date.today().year)
        serializer = ProjectLocationSerializer(
            ProjectLocationService.list_all_for_coordinator(),
            many=True,
            context={
                "finance_year": year,
                "for_coordinator": True,
            },
        )
        return Response(serializer.data)
