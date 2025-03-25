from ..BaseViewSet import BaseViewSet
from django.utils.decorators import method_decorator
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from infraohjelmointi_api.serializers import ProjectLocationSerializer
from rest_framework import status
from django.http import StreamingHttpResponse
from .utils import generate_response, generate_streaming_response

from drf_yasg.utils import swagger_auto_schema

@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_description="""
    `GET /api/locations/`

    Get all locations.

    The projectLocation data on projects shows the lowest location category from the class hierarchy, and it might be empty.
    To get detailed location information for projects, use the projectDistrict data and the endpoint `/api/districts/`.
    """
))
class ApiLocationsViewSet(BaseViewSet):
    http_method_names = ['get']

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = ProjectLocationSerializer

    @swagger_auto_schema(
        operation_description = """
        `GET /api/locations/{id}`

        Get specific location data.

        The projectLocation data on projects shows the lowest location category from the class hierarchy, and it might be empty.
        To get detailed location information for projects, use the projectDistrict data and the endpoint `/api/districts/`.
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
