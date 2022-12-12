import uuid
from rest_framework import viewsets
from .serializers import (
    ProjectCreateSerializer,
    ProjectGetSerializer,
    ProjectSetGetSerializer,
    ProjectSetCreateSerializer,
    ProjectTypeSerializer,
    PersonSerializer,
    ProjectAreaSerializer,
    BudgetItemSerializer,
    TaskSerializer,
    ProjectPhaseSerializer,
    ProjectPrioritySerializer,
    TaskStatusSerializer,
    NoteSerializer,
)
from .paginations import StandardResultsSetPagination
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import json
from rest_framework import status
from rest_framework.decorators import action

from django.core import serializers
from overrides import override


class BaseViewSet(viewsets.ModelViewSet):
    @override
    def get_queryset(self):
        """
        Overriden ModelViewSet class method to get appropriate queryset using serializer class
        """
        return self.get_serializer_class().Meta.model.objects.all()


class ProjectViewSet(BaseViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """

    permission_classes = []
    pagination_class = StandardResultsSetPagination

    @override
    def get_serializer_class(self):
        """
        Overriden ModelViewSet class method to get appropriate serializer depending on the request action
        """
        if self.action == "list":
            return ProjectGetSerializer
        if self.action == "retrieve":
            return ProjectGetSerializer
        return ProjectCreateSerializer

    @action(methods=["get"], detail=True, url_path=r"notes")
    def get_project_notes(self, request, pk):
        """
        Custom action to get Notes linked with a Project
        """
        try:
            uuid.UUID(str(pk))  # validating UUID
            instance = self.get_object()
            qs = NoteSerializer(instance.note_set, many=True).data
            return Response(qs)
        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )


class TaskStatusViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """

    permission_classes = []
    serializer_class = TaskStatusSerializer


class ProjectTypeViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectTypeSerializer


class ProjectPhaseViewSet(BaseViewSet):
    """
    API endpoint that allows project phase to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectPhaseSerializer


class ProjectPriorityViewSet(BaseViewSet):
    """
    API endpoint that allows project Priority to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectPrioritySerializer


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
    API endpoint that allows persons to be viewed or edited.
    """

    permission_classes = []
    serializer_class = PersonSerializer


class ProjectSetViewSet(BaseViewSet):
    """
    API endpoint that allows project sets to be viewed or edited.
    """

    permission_classes = []

    @override
    def get_serializer_class(self):
        """
        Overriden ModelViewSet class method to get appropriate serializer depending on the request action
        """
        if self.action == "list":
            return ProjectSetGetSerializer
        if self.action == "retrieve":
            return ProjectSetGetSerializer
        return ProjectSetCreateSerializer


class ProjectAreaViewSet(BaseViewSet):
    """
    API endpoint that allows project areas to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectAreaSerializer


class BudgetItemViewSet(BaseViewSet):
    """
    API endpoint that allows Budgets to be viewed or edited.
    """

    permission_classes = []
    serializer_class = BudgetItemSerializer


class TaskViewSet(BaseViewSet):
    """
    API endpoint that allows Tasks to be viewed or edited.
    """

    permission_classes = []
    serializer_class = TaskSerializer


class NoteViewSet(BaseViewSet):

    """
    API endpoint that allows notes to be viewed or edited.
    """

    permission_classes = []
    serializer_class = NoteSerializer

    @action(methods=["get"], detail=True, url_path=r"history")
    def history(self, request, pk):
        """
        Custom action to get history of a specific Note
        """
        try:
            uuid.UUID(str(pk))  # validating UUID
            instance = self.get_object()
            qs = instance.history.all().values()
            return Response(qs)
        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(methods=["get"], detail=True, url_path=r"history/(?P<userId>[-\w]+)")
    def history_user(self, request, pk, userId):
        """
        Custom action to get history of a specific Note filtered by a specific User
        """
        try:
            uuid.UUID(str(userId))
            uuid.UUID(str(pk))
            instance = self.get_object()
            qs = instance.history.all().filter(updatedBy_id=userId).values()
            return Response(qs)
        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )
