from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectGroupSerializer import (
    ProjectGroupSerializer,
)
from overrides import override
from rest_framework.response import Response
from datetime import date
from rest_framework.decorators import action


class ProjectGroupViewSet(BaseViewSet):
    """
    API endpoint that allows Project Groups to be viewed or edited.
    """

    serializer_class = ProjectGroupSerializer

    @override
    def list(self, request, *args, **kwargs):
        """
        Overriden list action to get a list of ProjectGroup

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Groups with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-groups/?year=<year>

            Returns
            -------

            JSON
                List of ProjectGroup instances with financial sums for projects under each group
        """
        year = request.query_params.get("year", date.today().year)
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True, context={"finance_year": year})

        return Response(serializer.data)

    @override
    def destroy(self, request, *args, **kwargs):
        """
        Overriding destroy action to get the deleted group id as a response
        """
        group = self.get_object()
        data = group.id
        group.delete()
        return Response({"id": data})

    @action(
        methods=["get"],
        detail=False,
        url_path=r"coordinator",
        name="get_groups_for_coordinator",
    )
    def get_groups_for_coordinator(self, request):
        """
        Custom action to get ProjectGroup instances with coordinator location/classes

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Groups with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-groups/coordinator/?year=<year>

            Returns
            -------

            JSON
                List of ProjectGroup instances with financial sums for projects under each group
        """
        year = request.query_params.get("year", date.today().year)
        qs = self.get_queryset().select_related(
            "classRelation",
            "locationRelation",
            "classRelation__coordinatorClass",
            "locationRelation__coordinatorLocation",
            "classRelation__parent__coordinatorClass",
            "locationRelation__parent__coordinatorLocation",
            "locationRelation__parent__parent__coordinatorLocation",
        )
        serializer = self.get_serializer(
            qs, many=True, context={"finance_year": year, "for_coordinator": True}
        )
        return Response(serializer.data)

    serializer_class = ProjectGroupSerializer
