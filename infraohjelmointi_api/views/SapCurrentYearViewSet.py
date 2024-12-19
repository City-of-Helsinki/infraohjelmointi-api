from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.SapCurrentYearSerializer import SapCurrentYearSerializer
from rest_framework.decorators import action
import logging
from overrides import override
from rest_framework.response import Response
from infraohjelmointi_api.services.SapCurrentYearService import SapCurrentYearService

logger = logging.getLogger("infraohjelmointi_api")


class SapCurrentYearViewSet(BaseViewSet):
    """
    API endpoint that allows Sap Cost to be viewed or edited.
    """

    serializer_class = SapCurrentYearSerializer
    http_method_names = ["get"]

    @action(
        methods=["get"],
        detail=False,
        url_path=r"(?P<year>[0-9]{4})",
        name="get_current_year_sap_cost_by_year",
    )
    def get_current_year_sap_cost_by_year(self, request, year):
        """
        Custom action to get current year's sap costs by year

            URL Parameters
            ----------

            year : int

            Usage
            ----------

            sap-current-year-costs/<year>/

            Returns
            -------

            JSON
                List of sap costs from the year provided
        """

        qs = SapCurrentYearService.get_by_year(int(year))
        serializer = self.get_serializer(qs, many=True)

        return Response(serializer.data)