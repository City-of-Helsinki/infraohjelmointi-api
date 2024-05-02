from ..BaseViewSet import BaseViewSet
from django.utils.decorators import method_decorator
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from infraohjelmointi_api.models import Project
from infraohjelmointi_api.serializers import ProjectGetSerializer
import uuid
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema

@method_decorator(name='list', decorator=swagger_auto_schema(
    operation_description="""
    `GET /api/projects/`

    Get all projects.
    """
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
        except:
            return Response(
                data={"message": "Not found"}, status=status.HTTP_404_NOT_FOUND
            )
