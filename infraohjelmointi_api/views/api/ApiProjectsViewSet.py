from ..BaseViewSet import BaseViewSet
from django.utils.decorators import method_decorator
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from infraohjelmointi_api.models import Project, ProjectClass
from infraohjelmointi_api.serializers import ProjectGetSerializer
import uuid
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

class_parameter = openapi.Parameter(
    'class',
    in_=openapi.IN_QUERY,
    description='Get all projects by class ID',
    type=openapi.TYPE_STRING
)

@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_description="""
    `GET /api/projects/`

    Get all projects.
    """,
    manual_parameters=[class_parameter]
))
class ApiProjectsViewSet(BaseViewSet):
    http_method_names = ['get']

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Project.objects.all()
    serializer_class = ProjectGetSerializer


    @swagger_auto_schema(
            operation_description = """
            `GET /api/projects/{id}`

            Get a project.
            """,
            )
    def retrieve(self, request, pk=None):
        try:
            uuid.UUID(str(pk))
            queryset = self.get_queryset()
            obj = queryset.get(pk=pk)
            serializer = self.get_serializer(obj)
            return Response(serializer.data)
        except (Exception):
            return Response(
                data={"message": "Not found"}, status=status.HTTP_404_NOT_FOUND
            )


    def list(self, request, *args, **kwargs):
        project_class_id = self.request.query_params.get('class')
        queryset = self.queryset
        if project_class_id is not None:
            queryset = queryset.filter(projectClass__id=uuid.UUID(project_class_id))
        self.queryset = queryset
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)
