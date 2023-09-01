from datetime import date
from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectLocationSerializer import (
    ProjectLocationSerializer,
)
from infraohjelmointi_api.services import (
    ProjectLocationService,
    LocationFinancialService,
)
from overrides import override
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status


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

    def is_patch_data_valid(self, data):
        """
        Utility function to validate patch data sent to the custom PATCH endpoint for coordinator location finances
        """
        finances = data.get("finances", None)
        if finances == None:
            return False

        parameters = finances.keys()
        if "year" not in parameters:
            return False

        for param in parameters:
            if param == "year":
                continue
            values = finances[param]
            values_length = len(values.keys())

            if type(values) != dict:
                return False
            if values_length == 0 or values_length > 2:
                return False
            if not "frameBudget" in values and not "budgetChange" in values:
                return False

        return True

    @action(
        methods=["patch"],
        detail=False,
        url_path=r"coordinator/(?P<location_id>[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12})",
    )
    def patch_coordinator_location_finances(self, request, location_id):
        """
        Custom PATCH endpoint for coordinator locations **finances ONLY**

            URL Parameters
            ----------

            location_id : UUID string

            Coordinator location Id

            Usage
            ----------

            project-locations/coordinator/<location_id>/

            Returns
            -------

            JSON
                Patched coordinator ProjectLocation Instance
        """
        if not ProjectLocationService.instance_exists(
            id=location_id, forCoordinatorOnly=True
        ):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not self.is_patch_data_valid(request.data):
            return Response(
                data={"message": "Invalid data format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        finances = request.data.get("finances")
        startYear = finances.get("year")
        for parameter in finances.keys():
            if parameter == "year":
                continue
            patchData = finances[parameter]
            year = LocationFinancialService.get_request_field_to_year_mapping(
                start_year=startYear
            ).get(parameter, None)

            if year == None:
                return Response(
                    data={"message": "Invalid data format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        LocationFinancialService.update_or_create(
            year=year, location_id=location_id, updatedData=patchData
        )
        return Response(
            ProjectLocationSerializer(
                ProjectLocationService.get_by_id(id=location_id),
                context={
                    "finance_year": startYear,
                    "for_coordinator": True,
                },
            ).data
        )
