from datetime import date
from .BaseViewSet import BaseViewSet
from overrides import override
from rest_framework.response import Response


class BaseClassLocationViewSet(BaseViewSet):
    """
    Base class for class and location viewsets
    """

    @override
    def list(self, request, *args, **kwargs):
        """
        Overriden list action to get a list of ProjectClass

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Class/Location with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-classes/?year=<year>

            or

            project-locations/?year=<year>

            Returns
            -------

            JSON
                List of ProjectClass/ProjectLocation instances with financial sums for projects under each instance
        """
        year = request.query_params.get("year", date.today().year)
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True, context={"finance_year": year})

        return Response(serializer.data)

    def is_patch_data_valid(self, data):
        """
        Utility function to validate patch data sent to the custom PATCH endpoint for coordinator class/location finances
        """
        finances = data.get("finances", None)
        if finances == None:
            return False

        parameters = list(finances.keys())
        if "year" not in parameters:
            return False
        parameters.remove("year")

        for param in parameters:
            values = finances[param]
            values_length = len(values.keys())

            if not isinstance(values, dict):
                return False
            if values_length == 0 or values_length > 2:
                return False
            if "frameBudget" not in values and "budgetChange" not in values:
                return False

        return True
