import uuid
from infraohjelmointi_api.models import (
    Project,
    ProjectClass,
    ProjectGroup,
    ProjectLocation,
)
from rest_framework.exceptions import APIException
import django_filters
from django.db.models import Q
from django.db.models.expressions import RawSQL
from distutils.util import strtobool
import datetime
from rest_framework.pagination import PageNumberPagination
from itertools import chain
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
    ProjectGroupSerializer,
    ProjectLockSerializer,
    searchResultSerializer,
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
from django.db.models import Count, Case, When


class BaseViewSet(viewsets.ModelViewSet):
    @override
    def get_queryset(self):
        """
        Overriden ModelViewSet class method to get appropriate queryset using serializer class
        """
        return self.get_serializer_class().Meta.model.objects.all()


class ProjectLockViewSet(BaseViewSet):
    """
    API endpoint that allows Project Lock status to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectLockSerializer


class ProjectHashtagViewSet(BaseViewSet):
    """
    API endpoint that allows Project Hashtags to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectHashtagSerializer

    @override
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        popularQs = (
            qs.annotate(usage_count=Count("relatedProject"))
            .filter(usage_count__gt=0)
            .order_by("-usage_count")[:15]
        )

        serializer = self.get_serializer(qs, many=True)
        popularSerializer = self.get_serializer(popularQs, many=True)
        return Response(
            {"hashTags": serializer.data, "popularHashTags": popularSerializer.data}
        )


class ProjectGroupViewSet(BaseViewSet):
    """
    API endpoint that allows Project Groups to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectGroupSerializer


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

    hashtag = django_filters.ModelMultipleChoiceFilter(
        field_name="hashTags",
        queryset=ProjectHashtagSerializer.Meta.model.objects.all(),
    )

    programmed = django_filters.TypedMultipleChoiceFilter(
        choices=(
            ("false", "False"),
            ("true", "True"),
        ),
        coerce=strtobool,
    )

    class Meta:
        fields = {
            "hkrId": ["exact"],
            "category": ["exact"],
            "phase": ["exact"],
            "personPlanning": ["exact"],
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
    def list(self, request, *args, **kwargs):
        response = {}
        freeSearch = request.query_params.get("freeSearch", None)
        projectGroup = request.query_params.getlist("group", [])
        masterClass = self.request.query_params.getlist("masterClass", [])
        _class = self.request.query_params.getlist("class", [])
        subClass = self.request.query_params.getlist("subClass", [])

        mainDistrict = self.request.query_params.getlist("mainDistrict", [])
        district = self.request.query_params.getlist("district", [])
        subDistrict = self.request.query_params.getlist("subDistrict", [])

        hkrId = request.query_params.get("hkrId", None)
        category = request.query_params.get("category", None)
        hashTags = request.query_params.getlist("hashtag", [])
        phase = request.query_params.get("phase", None)
        personPlanning = request.query_params.get("personPlanning", None)
        programmed = request.query_params.getlist("programmed", [])
        projects = self.request.query_params.getlist("project", [])
        inGroup = self.request.query_params.get("inGroup", None)
        projectName = self.request.query_params.get("projectName", None)
        order = self.request.query_params.get("order", None)
        limit = self.request.query_params.get("limit", "10")

        if freeSearch is not None:
            if freeSearch == "":
                return Response(
                    {
                        "projects": [],
                        "hashtags": [],
                        "groups": [],
                    }
                )

            hashTagQs = ProjectHashtagSerializer.Meta.model.objects.filter(
                value__icontains=freeSearch
            )
            projectQs = ProjectGetSerializer.Meta.model.objects.filter(
                name__icontains=freeSearch
            )
            projectGroupQs = ProjectGroupSerializer.Meta.model.objects.filter(
                name__icontains=freeSearch
            )
            hashTagsSerializer = ProjectHashtagSerializer(
                hashTagQs, fields=("id", "value"), many=True
            )
            projectsSerializer = ProjectGetSerializer(
                projectQs, fields=("id", "name"), many=True
            )
            projectGroupsSerializer = ProjectGroupSerializer(
                projectGroupQs, fields=("id", "name"), many=True
            )

            return Response(
                {
                    "projects": [
                        {"id": project["id"], "value": project["name"]}
                        for project in projectsSerializer.data
                    ],
                    "hashtags": hashTagsSerializer.data,
                    "groups": [
                        {"id": group["id"], "value": group["name"]}
                        for group in projectGroupsSerializer.data
                    ],
                }
            )
        elif (
            len(projects) > 0
            or len(projectGroup) > 0
            or len(masterClass) > 0
            or len(_class) > 0
            or len(subClass) > 0
            or len(mainDistrict) > 0
            or len(district) > 0
            or len(subDistrict) > 0
            or len(hashTags) > 0
            or len(programmed) > 0
            or hkrId is not None
            or category is not None
            or phase is not None
            or personPlanning is not None
            or (inGroup is not None and inGroup in ["true", "True", "false", "False"])
            or projectName is not None
            or order is not None
        ):
            if not limit.isnumeric() or limit not in ["10", "20", "30"]:
                raise APIException(detail="Invalid value for limit parameter")
            limit = int(limit)
            # already filtered queryset
            queryset = self.filter_queryset(self.get_queryset())
            groups = []
            projectClasses = []
            projectLocations = []
            combinedQuerysets = []

            if order is None:
                order = "new"

            if len(projectGroup) > 0:
                groups = ProjectGroup.objects.filter(
                    id__in=queryset.values_list("projectGroup", flat=True).distinct()
                ).select_related("classRelation")

            if len(masterClass) > 0 or len(_class) > 0 or len(subClass) > 0:
                projectClasses = ProjectClass.objects.filter(
                    id__in=queryset.values_list("projectClass", flat=True).distinct()
                )
            if len(mainDistrict) > 0 or len(district) > 0 or len(subDistrict) > 0:
                projectLocations = ProjectLocation.objects.filter(
                    id__in=queryset.values_list("projectLocation", flat=True).distinct()
                )

            if order == "new":
                combinedQuerysets = sorted(
                    chain(groups, projectClasses, projectLocations, queryset),
                    key=lambda obj: obj.createdDate,
                    reverse=True,
                )
            elif order == "old":
                combinedQuerysets = sorted(
                    chain(groups, projectClasses, projectLocations, queryset),
                    key=lambda obj: obj.createdDate,
                    reverse=False,
                )
            elif order == "project":
                combinedQuerysets = list(
                    chain(queryset, projectClasses, projectLocations, groups)
                )
            elif order == "group":
                combinedQuerysets = list(
                    chain(queryset, projectClasses, projectLocations, groups)
                )
            elif order == "phase":
                queryset = queryset.annotate(
                    relevancy=Count(Case(When(phase__value="proposal", then=1)))
                ).order_by("-relevancy")
                combinedQuerysets = list(
                    chain(
                        queryset,
                        groups,
                        projectClasses,
                        projectLocations,
                    )
                )
            else:
                return Response(
                    data={"message": "Invalid order"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            searchPaginator = PageNumberPagination()
            searchPaginator.page_size = limit
            result = searchPaginator.paginate_queryset(combinedQuerysets, request)
            serializer = searchResultSerializer(
                result, many=True, context={"hashtags_include": hashTags}
            )
            response = {
                "next": searchPaginator.get_next_link(),
                "previous": searchPaginator.get_previous_link(),
                "count": searchPaginator.page.paginator.count,
                "results": serializer.data,
            }

            return Response(response)

        else:
            # with filter
            queryset = self.filter_queryset(self.get_queryset())
            # pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

    @override
    def get_queryset(self):

        qs = super().get_queryset()
        masterClass = self.request.query_params.getlist("masterClass", [])
        _class = self.request.query_params.getlist("class", [])
        subClass = self.request.query_params.getlist("subClass", [])

        mainDistrict = self.request.query_params.getlist("mainDistrict", [])
        district = self.request.query_params.getlist("district", [])
        subDistrict = self.request.query_params.getlist("subDistrict", [])

        prYearMin = self.request.query_params.get("prYearMin", None)
        prYearMax = self.request.query_params.get("prYearMax", None)
        projects = self.request.query_params.getlist("project", [])
        projectGroups = self.request.query_params.getlist("group", [])
        inGroup = self.request.query_params.get("inGroup", None)
        projectName = self.request.query_params.get("projectName", None)

        try:
            if projectName is not None:
                qs = qs.filter(name__icontains=projectName)

            if inGroup is not None:
                if inGroup in ["true", "True"]:
                    qs = qs.filter(projectGroup__isnull=False)
                elif inGroup in ["false", "False"]:
                    qs = qs.filter(projectGroup__isnull=True)

            if len(projects) > 0:
                qs = qs.filter(id__in=projects)
            qs = self._filter_projects_by_programming_year(
                qs, prYearMin=prYearMin, prYearMax=prYearMax
            )
            if len(projectGroups) > 0:
                qs = qs.filter(projectGroup__in=projectGroups)
            if len(masterClass) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=False,
                    has_parent_parent=False,
                    search_ids=masterClass,
                    model_class=ProjectClass,
                )

            if len(_class) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=False,
                    search_ids=_class,
                    model_class=ProjectClass,
                )

            if len(subClass) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=True,
                    search_ids=subClass,
                    model_class=ProjectClass,
                )

            if len(mainDistrict) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=False,
                    has_parent_parent=False,
                    search_ids=mainDistrict,
                    model_class=ProjectLocation,
                )
            if len(district) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=False,
                    search_ids=district,
                    model_class=ProjectLocation,
                )
            if len(subDistrict) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=True,
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
        self, qs, has_parent: bool, has_parent_parent: bool, search_ids, model_class
    ):
        paths = (
            model_class.objects.filter(
                id__in=search_ids,
                parent__isnull=not has_parent,
                parent__parent__isnull=not has_parent_parent,
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

        if model_class.__name__ == "ProjectLocation":
            return qs.filter(projectLocation__in=ids)
        elif model_class.__name__ == "ProjectClass":
            return qs.filter(projectClass__in=ids)

    def _filter_projects_by_programming_year(self, qs, prYearMin, prYearMax):
        currYear = datetime.date.today().year
        yearToFieldMapping = {
            currYear: "budgetForecast1CurrentYear__gt",
            currYear + 1: "budgetProposalCurrentYearPlus1__gt",
            currYear + 2: "budgetProposalCurrentYearPlus2__gt",
            currYear + 3: "preliminaryCurrentYearPlus3__gt",
            currYear + 4: "preliminaryCurrentYearPlus4__gt",
            currYear + 5: "preliminaryCurrentYearPlus5__gt",
            currYear + 6: "preliminaryCurrentYearPlus6__gt",
            currYear + 7: "preliminaryCurrentYearPlus7__gt",
            currYear + 8: "preliminaryCurrentYearPlus8__gt",
            currYear + 9: "preliminaryCurrentYearPlus9__gt",
            currYear + 10: "preliminaryCurrentYearPlus10__gt",
        }
        if prYearMin is not None and prYearMax is not None:
            if not prYearMax.isnumeric() or not prYearMin.isnumeric():
                raise APIException(detail="Invalid value for prYearMin or prYearMax")
            else:
                prYearMin = int(prYearMin)
                prYearMax = int(prYearMax)
                if prYearMin > prYearMax:
                    raise APIException(
                        detail="prYearMin cannot be greater than prYearMax"
                    )
                if (
                    prYearMin in yearToFieldMapping.keys()
                    and prYearMax in yearToFieldMapping.keys()
                ):
                    qs = qs.filter(
                        Q(
                            *[
                                (yearToFieldMapping[year], 0)
                                for year in range(prYearMin, prYearMax + 1, 1)
                            ],
                            _connector=Q.OR
                        )
                        & Q(programmed=True)
                    )
                elif prYearMin in yearToFieldMapping.keys():
                    qs = qs.filter(
                        Q(
                            *[
                                (yearToFieldMapping[year], 0)
                                for year in range(prYearMin, currYear + 11, 1)
                            ],
                            _connector=Q.OR
                        )
                        & Q(programmed=True)
                    )
                elif prYearMax in yearToFieldMapping.keys():
                    qs = qs.filter(
                        Q(
                            *[
                                (yearToFieldMapping[year], 0)
                                for year in range(currYear, prYearMax + 1, 1)
                            ],
                            _connector=Q.OR
                        )
                        & Q(programmed=True)
                    )
                else:
                    qs = qs.none()

        elif prYearMin is not None:
            if not prYearMin.isnumeric():
                raise APIException(detail="Invalid value for prYearMin")
            else:
                prYearMin = int(prYearMin)
                if prYearMin < currYear:
                    qs = qs.filter(
                        Q(
                            *[
                                (yearToFieldMapping[year], 0)
                                for year in range(currYear, currYear + 11, 1)
                            ],
                            _connector=Q.OR
                        )
                        & Q(programmed=True)
                    )
                elif prYearMin > currYear + 10:
                    qs = qs.none()
                else:
                    qs = qs.filter(
                        Q(
                            *[
                                (yearToFieldMapping[year], 0)
                                for year in range(prYearMin, currYear + 11, 1)
                            ],
                            _connector=Q.OR
                        )
                        & Q(programmed=True)
                    )
        elif prYearMax is not None:
            if not prYearMax.isnumeric():
                raise APIException(detail="Invalid value for prYearMax")
            else:
                prYearMax = int(prYearMax)
                if prYearMax < currYear:
                    qs = qs.none()
                elif prYearMax > currYear + 10:
                    qs = qs.filter(
                        Q(
                            *[
                                (yearToFieldMapping[year], 0)
                                for year in range(currYear, currYear + 11, 1)
                            ],
                            _connector=Q.OR
                        )
                        & Q(programmed=True)
                    )
                else:
                    qs = qs.filter(
                        Q(
                            *[
                                (yearToFieldMapping[year], 0)
                                for year in range(currYear, prYearMax + 1, 1)
                            ],
                            _connector=Q.OR
                        )
                        & Q(programmed=True)
                    )
        return qs


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
