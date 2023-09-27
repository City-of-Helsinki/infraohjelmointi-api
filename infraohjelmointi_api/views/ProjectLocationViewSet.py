from datetime import date
from infraohjelmointi_api.serializers.ProjectLocationSerializer import (
    ProjectLocationSerializer,
)
from infraohjelmointi_api.services import (
    ProjectLocationService,
    LocationFinancialService,
)
from infraohjelmointi_api.models.LocationFinancial import LocationFinancial
from overrides import override
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from .BaseClassLocationViewSet import BaseClassLocationViewSet
from rest_framework.exceptions import ParseError


class ProjectLocationViewSet(BaseClassLocationViewSet):
    """
    API endpoint that allows Project Locations to be viewed or edited.
    """

    serializer_class = ProjectLocationSerializer

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

            forcedToFrame (optional) : bool

            Query param to fetch coordinator locations with frameView project sums
            Defaults to False.

            Usage
            ----------

            project-locations/coordinator/?year=<year>&forcedToFrame=<bool>

            Returns
            -------

            JSON
                List of ProjectLocation instances with financial sums for projects under each location
        """
        year = request.query_params.get("year", date.today().year)
        forcedToFrame = request.query_params.get("forcedToFrame", False)
        if forcedToFrame in ["False", "false"]:
            forcedToFrame = False

        if forcedToFrame in ["true", "True"]:
            forcedToFrame = True

        if forcedToFrame not in [True, False]:
            raise ParseError(
                detail={"forcedToFrame": "Value must be a boolean"}, code="invalid"
            )
        serializer = ProjectLocationSerializer(
            ProjectLocationService.list_all_for_coordinator(),
            many=True,
            context={
                "finance_year": year,
                "for_coordinator": True,
                "forcedToFrame": forcedToFrame,
            },
        )
        return Response(serializer.data)

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
        # not using LocationFinancial Service here to manually be able to add finance_year to the instance which
        # will be sent to post_save signal
        try:
            obj = LocationFinancial.objects.get(
                year=year, locationRelation_id=location_id
            )
            for key, value in patchData.items():
                setattr(obj, key, value)
            obj.finance_year = startYear
            obj.save()
        except LocationFinancial.DoesNotExist:
            obj = LocationFinancial(
                **patchData, year=year, locationRelation_id=location_id
            )
            obj.finance_year = startYear
            obj.save()
        return Response(
            ProjectLocationSerializer(
                ProjectLocationService.get_by_id(id=location_id),
                context={
                    "finance_year": startYear,
                    "for_coordinator": True,
                },
            ).data
        )
