from datetime import date
from collections import defaultdict
from ..BaseViewSet import BaseViewSet
from django.utils.decorators import method_decorator
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from infraohjelmointi_api.serializers import ProjectClassSerializer
from infraohjelmointi_api.models import (
    LocationFinancial, ClassFinancial
)
from django.http import StreamingHttpResponse
from django.db.models import F
from .utils import generate_response, generate_streaming_response, send_logger_api_generate_data_start

from drf_yasg.utils import swagger_auto_schema


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="""
    `GET /api/classes/`

    Get all classes.
    """
    ),
)
class ApiClassesViewSet(BaseViewSet):
    http_method_names = ["get"]

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = ProjectClassSerializer

    @swagger_auto_schema(
        operation_description="""
            `GET /api/classes/{id}`

            Get specific project class data.
            """,
    )
    def retrieve(self, request, pk=None):
        return generate_response(self, request.user.id, pk, request.path)

    def list(self, request, *args, **kwargs):
        send_logger_api_generate_data_start(request.user.id, request.path)
        queryset = self.get_queryset()

        year = date.today().year      
        class_financials = ClassFinancial.objects.filter(
            year__in=range(year, year+11)
        ).annotate(relation=F("classRelation")).values("year", "relation", "frameBudget")
        location_financials = LocationFinancial.objects.filter(
            year__in=range(year, year+11)
        ).annotate(relation=F("locationRelation")).values("year", "relation", "frameBudget")
        financials = class_financials.union(location_financials)
        frame_budgets = defaultdict(lambda: 0)
        for f in financials:
            frame_budgets[f"{f['year']}-{f['relation']}"] = f["frameBudget"]

        return StreamingHttpResponse(
            generate_streaming_response(
                queryset,
                self.serializer_class,
                request.user.id,
                request.path,
                serializer_context={"frame_budgets": frame_budgets}
            ),
            content_type="application/json",
        )
