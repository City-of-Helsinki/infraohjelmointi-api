from rest_framework import viewsets
from .serializers import (
    ProjectSerializer,
    ProjectTypeSerializer,
    PersonSerializer,
    ProjectSetSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
import json


class BaseViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.all()


class ProjectViewSet(BaseViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectSerializer


class ProjectTypeViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectTypeSerializer


class MockProjectViewSet(viewsets.ViewSet):
    """
    API endpoint that returns mock project data.
    """

    mock_data = json.load(
        open("./infraohjelmointi_api/mock_data/hankekortti.json", "r")
    )

    def list(self, request):
        queryset = self.mock_data
        return Response(queryset)


class PersonViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """

    permission_classes = []
    serializer_class = PersonSerializer


class ProjectSetViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectSetSerializer
