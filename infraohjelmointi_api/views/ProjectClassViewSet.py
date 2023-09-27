from datetime import date
from .BaseClassLocationViewSet import BaseClassLocationViewSet
from infraohjelmointi_api.serializers.ProjectClassSerializer import (
    ProjectClassSerializer,
)
from infraohjelmointi_api.models.ClassFinancial import ClassFinancial
from infraohjelmointi_api.services import ProjectClassService, ClassFinancialService
from overrides import override
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.exceptions import ParseError


class ProjectClassViewSet(BaseClassLocationViewSet):
    """
    API endpoint that allows Project Classes to be viewed or edited.
    """

    serializer_class = ProjectClassSerializer

    @override
    def get_queryset(self):
        """Default is programmer view"""
        return (
            ProjectClassService.list_all()
            .select_related("coordinatorClass")
            .prefetch_related("coordinatorClass__finances")
        )

    @action(methods=["get"], detail=False, url_path=r"coordinator")
    def list_for_coordinator(self, request):
        """
        Overriden list action to get a list of coordinator ProjectClass

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Class with finances starting from this year.
            Defaults to current year.

            forcedToFrame (optional) : bool

            Query param to fetch coordinator classes with frameView project sums.
            Defaults to False.

            Usage
            ----------

            project-classes/?year=<year>&forcedToframe=<bool>

            Returns
            -------

            JSON
                List of ProjectClass instances with financial sums for projects under each class
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
        serializer = ProjectClassSerializer(
            ProjectClassService.list_all_for_coordinator()
            .prefetch_related("coordinatorClass__finances")
            .select_related("coordinatorClass"),
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
        url_path=r"coordinator/(?P<class_id>[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12})",
    )
    def patch_coordinator_class_finances(self, request, class_id):
        """
        Custom PATCH endpoint for coordinator classes **finances ONLY**

            URL Parameters
            ----------

            class_id : UUID string

            Coordinator class Id

            Usage
            ----------

            project-classes/coordinator/<class_id>/

            Returns
            -------

            JSON
                Patched coordinator ProjectClass Instance
        """
        if not ProjectClassService.instance_exists(
            id=class_id, forCoordinatorOnly=True
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
            year = ClassFinancialService.get_request_field_to_year_mapping(
                start_year=startYear
            ).get(parameter, None)

            if year == None:
                return Response(
                    data={"message": "Invalid data format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        # not using ClassFinancial Service here to manually be able to add finance_year to the instance which
        # will be sent to post_save signal
        try:
            obj = ClassFinancial.objects.get(year=year, classRelation_id=class_id)
            for key, value in patchData.items():
                setattr(obj, key, value)
            obj.finance_year = startYear
            obj.save()
        except ClassFinancial.DoesNotExist:
            obj = ClassFinancial(**patchData, year=year, classRelation_id=class_id)
            obj.finance_year = startYear
            obj.save()

        return Response(
            ProjectClassSerializer(
                ProjectClassService.get_by_id(id=class_id),
                context={
                    "finance_year": startYear,
                    "for_coordinator": True,
                },
            ).data
        )
