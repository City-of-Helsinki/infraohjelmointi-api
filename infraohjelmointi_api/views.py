import uuid
from infraohjelmointi_api.models import Project, ProjectClass, ProjectLocation
from rest_framework.exceptions import APIException
import django_filters
from django.db.models import Q
from django.db.models.expressions import RawSQL
from distutils.util import strtobool

from rest_framework import viewsets
from .serializers import (
    NoteCreateSerializer,
    NoteHistorySerializer,
    ProjectCreateSerializer,
    ProjectGetSerializer,
    ProjectNoteGetSerializer,
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
    ConstructionPhaseDetailSerializer,
    ProjectCategorySerializer,
    ProjectRiskSerializer,
    NoteGetSerializer,
    ConstructionPhaseSerializer,
    PlanningPhaseSerializer,
    NoteUpdateSerializer,
    ProjectQualityLevelSerializer,
    ProjectLocationSerializer,
    ProjectClassSerializer,
    ProjectResponsibleZoneSerializer,
    ProjectHashtagSerializer,
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
from django_filters.rest_framework import DjangoFilterBackend


class BaseViewSet(viewsets.ModelViewSet):
    @override
    def get_queryset(self):
        """
        Overriden ModelViewSet class method to get appropriate queryset using serializer class
        """
        return self.get_serializer_class().Meta.model.objects.all()


class ProjectHashtagViewSet(BaseViewSet):
    """
    API endpoint that allows Project Hashtags to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectHashtagSerializer


class ProjectLocationViewSet(BaseViewSet):
    """
    API endpoint that allows Project Locations to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectLocationSerializer


class ProjectClassViewSet(BaseViewSet):
    """
    API endpoint that allows Project Classes to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectClassSerializer


class ProjectQualityLevelViewSet(BaseViewSet):
    """
    API endpoint that allows Project quality levels to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectQualityLevelSerializer


class PlanningPhaseViewSet(BaseViewSet):
    """
    API endpoint that allows Planning phases to be viewed or edited.
    """

    permission_classes = []
    serializer_class = PlanningPhaseSerializer


class ProjectResponsibleZoneViewSet(BaseViewSet):
    """
    API endpoint that allows Planning responsible zones to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectResponsibleZoneSerializer


class ConstructionPhaseViewSet(BaseViewSet):
    """
    API endpoint that allows Construction phases to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ConstructionPhaseSerializer


class ProjectFilter(django_filters.FilterSet):

    freeSearch = django_filters.CharFilter(
        method="filter_search_string", label="Search"
    )
    programmed = django_filters.TypedMultipleChoiceFilter(
        choices=(
            ("false", "False"),
            ("true", "True"),
        ),
        coerce=strtobool,
    )

    def filter_search_string(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) | Q(hashTags__value__icontains=value)
        ).distinct()

    class Meta:
        fields = {
            "hkrId": ["exact"],
            "category": ["exact"],
        }
        model = Project


class ProjectViewSet(BaseViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """

    permission_classes = []
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectFilter

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

    @override
    def get_queryset(self):
        qs = super().get_queryset()
        masterClass = self.request.query_params.getlist("masterClass", [])
        _class = self.request.query_params.getlist("class", [])
        subClass = self.request.query_params.getlist("subClass", [])

        mainDistrict = self.request.query_params.getlist("mainDistrict", [])
        district = self.request.query_params.getlist("district", [])
        subDistrict = self.request.query_params.getlist("subDistrict", [])

        try:
            if len(masterClass) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=False,
                    has_children=True,
                    search_ids=masterClass,
                    model_class=ProjectClass,
                )

            if len(_class) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_children=True,
                    search_ids=_class,
                    model_class=ProjectClass,
                )

            if len(subClass) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_children=False,
                    search_ids=subClass,
                    model_class=ProjectClass,
                )

            if len(mainDistrict) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=False,
                    has_children=True,
                    search_ids=mainDistrict,
                    model_class=ProjectLocation,
                )
            if len(district) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_children=True,
                    search_ids=district,
                    model_class=ProjectLocation,
                )
            if len(subDistrict) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_children=False,
                    search_ids=subDistrict,
                    model_class=ProjectLocation,
                )

            return qs
        except Exception as e:
            raise APIException(detail={"message": e})

    @action(methods=["get"], detail=True, url_path=r"notes")
    def get_project_notes(self, request, pk):
        """
        Custom action to get Notes linked with a Project
        """
        try:
            uuid.UUID(str(pk))  # validating UUID
            instance = self.get_object()
            qs = ProjectNoteGetSerializer(
                instance.note_set.exclude(deleted=True), many=True
            ).data
            return Response(qs)
        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )

    def _filter_projects_by_hierarchy(
        self, qs, has_parent: bool, has_children: bool, search_ids, model_class
    ):

        paths = (
            model_class.objects.filter(
                id__in=search_ids,
                parent__isnull=not has_parent,
                childClass__isnull=not has_children,
            )
            .distinct()
            .values_list("path", flat=True)
        )

        ids = (
            model_class.objects.filter(
                Q(*[("path__startswith", path) for path in paths], _connector=Q.OR)
            )
            .distinct()
            .values_list("id", flat=True)
            if len(paths) > 0
            else []
        )
        if isinstance(model_class, ProjectLocation):
            return qs.filter(projectLocation__in=ids)
        elif isinstance(model_class, ProjectClass):
            return qs.filter(projectClass__in=ids)


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


class ConstructionPhaseDetailViewSet(BaseViewSet):
    """
    API endpoint that allows construction phase details to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ConstructionPhaseDetailSerializer


class ProjectCategoryViewSet(BaseViewSet):
    """
    API endpoint that allows project cetagories to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectCategorySerializer


class ProjectRiskViewSet(BaseViewSet):
    """
    API endpoint that allows project risk assessments to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectRiskSerializer


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

    @override
    def get_serializer_class(self):
        """
        Overriden ModelViewSet class method to get appropriate serializer depending on the request action
        """
        if self.action == "list":
            return NoteGetSerializer
        if self.action == "retrieve":
            return NoteGetSerializer
        if self.action == "create":
            return NoteCreateSerializer
        return NoteUpdateSerializer

    @action(methods=["get"], detail=True, url_path=r"history")
    def history(self, request, pk):
        """
        Custom action to get history of a specific Note
        """
        try:
            uuid.UUID(str(pk))  # validating UUID
            instance = self.get_object()
            qs = instance.history.all()
            serializer = NoteHistorySerializer(qs, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )

    @override
    def destroy(self, request, *args, **kwargs):
        """
        Overriding destroy action to soft delete note on DELETE request
        """
        note = self.get_object()
        data = note.id
        note.deleted = True
        note.save()
        return Response({"id": data})

    @action(methods=["get"], detail=True, url_path=r"history/(?P<userId>[-\w]+)")
    def history_user(self, request, pk, userId):
        """
        Custom action to get history of a specific Note filtered by a specific User
        """
        try:
            uuid.UUID(str(userId))
            uuid.UUID(str(pk))
            instance = self.get_object()
            qs = instance.history.all().filter(updatedBy_id=userId)
            serializer = NoteHistorySerializer(qs, many=True)
            return Response(serializer.data)

        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )
