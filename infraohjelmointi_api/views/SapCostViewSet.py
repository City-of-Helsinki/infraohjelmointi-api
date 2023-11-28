from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.SapCostSerializer import SapCostSerializer
from rest_framework.decorators import action
import logging
from overrides import override
from rest_framework.response import Response
from infraohjelmointi_api.services.SapCostService import SapCostService

logger = logging.getLogger("infraohjelmointi_api")


class SapCostViewSet(BaseViewSet):
    """
    API endpoint that allows Sap Cost to be viewed or edited.
    """

    serializer_class = SapCostSerializer
    http_method_names = ["get"]

    @override
    def list(self, request, *args, **kwargs):
        return self.retrieve(request=request, args=args, kwargs=kwargs)

    @action(
        methods=["get"],
        detail=False,
        url_path=r"(?P<year>[0-9]{4})",
        name="get_sap_costs_by_year",
    )
    def get_sap_cost_by_year(self, request, year):
        """
        Custom action to get sap cost by year

            URL Parameters
            ----------

            year : int

            Usage
            ----------

            sap-costs/<year>/

            Returns
            -------

            JSON
                List of sap costs from the year provided
        """

        qs = SapCostService.get_by_year(int(year))
        serializer = self.get_serializer(qs, many=True)

        return Response(serializer.data)
