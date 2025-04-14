from ..BaseViewSet import BaseViewSet
from django.utils.decorators import method_decorator
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from infraohjelmointi_api.serializers import ProjectGroupSerializer
from django.http import StreamingHttpResponse
from .utils import generate_response, generate_streaming_response, send_logger_api_generate_data_start

from drf_yasg.utils import swagger_auto_schema


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        operation_description="""
    `GET /api/groups/`

    Get all projects.
    """
    ),
)
class ApiGroupsViewSet(BaseViewSet):
    http_method_names = ["get"]

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = ProjectGroupSerializer

    @swagger_auto_schema(
        operation_description="""
            `GET /api/groups/{id}`

            Get specific project group data.
            """,
    )
    def retrieve(self, request, pk=None):
        return generate_response(self, request.user.id, pk, request.path)

    def list(self, request, *args, **kwargs):
        send_logger_api_generate_data_start(request.user.id, request.path)
        queryset = self.get_queryset()
        return StreamingHttpResponse(
            generate_streaming_response(
                queryset, self.serializer_class, request.user.id, request.path
            ),
            content_type="application/json",
        )
