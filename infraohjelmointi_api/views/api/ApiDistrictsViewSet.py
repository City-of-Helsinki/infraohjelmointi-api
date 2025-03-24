from ..BaseViewSet import BaseViewSet
from django.utils.decorators import method_decorator
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from infraohjelmointi_api.serializers import ProjectDistrictSerializer
from rest_framework import status
from django.http import StreamingHttpResponse
from .utils import generate_response, generate_streaming_response

from drf_yasg.utils import swagger_auto_schema

@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_description="""
    `GET /api/districts/`

    Get all districts. A district is the lowest level of location where a project is situated.
    """
))
class ApiDistrictsViewSet(BaseViewSet):
    http_method_names = ['get']

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = ProjectDistrictSerializer

    @swagger_auto_schema(
            operation_description = """
            `GET /api/districts/{id}`

            Get all project districts.
            """,
            )
    def retrieve(self, request, pk=None):
        try:
            return generate_response(self, request.user.id, pk, request.path)
        except Exception:
            return Response(
                data={"message": "Not found"}, status=status.HTTP_404_NOT_FOUND
            )

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return StreamingHttpResponse(
            generate_streaming_response(queryset, self.serializer_class, request.user.id, request.path),
            content_type='application/json'
        )
