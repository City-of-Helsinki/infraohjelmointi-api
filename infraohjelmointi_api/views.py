import time
import uuid
from datetime import date
from infraohjelmointi_api.models import (
    Project,
    ProjectClass,
    ProjectGroup,
    ProjectLocation,
    ProjectFinancial,
    ClassFinancial,
)
from infraohjelmointi_api.services.ProjectFinancialService import (
    ProjectFinancialService,
)
from infraohjelmointi_api.services.ClassFinancialService import (
    ClassFinancialService,
)
from rest_framework.exceptions import APIException, ParseError, ValidationError
from django.dispatch import receiver
import django_filters
from django.db.models import Q
from django.db.models.expressions import RawSQL
from distutils.util import strtobool
import datetime
from rest_framework.pagination import PageNumberPagination
from itertools import chain
from django.http.response import StreamingHttpResponse
from django.db.models.signals import post_save
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
    SearchResultSerializer,
    ProjectFinancialSerializer,
    ClassFinancialSerializer,
)
from .paginations import StandardResultsSetPagination
from .services import ProjectClassService, ProjectLocationService, ProjectWiseService
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import json
from rest_framework import status
from rest_framework.decorators import action

from django.db import transaction
from overrides import override
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Case, When
from django.shortcuts import get_object_or_404
from django.db import transaction
import logging


logger = logging.getLogger("infraohjelmointi_api")


class BaseViewSet(viewsets.ModelViewSet):
    @override
    def get_queryset(self):
        """
        Overriden ModelViewSet class method to get appropriate queryset using serializer class
        """
        return self.get_serializer_class().Meta.model.objects.all()


class ProjectFinancialViewSet(BaseViewSet):
    """
    API endpoint that allows Project Finances to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectFinancialSerializer

    @action(
        methods=["get"],
        detail=False,
        url_path=r"(?P<project>[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12})/(?P<year>[0-9]{4})",
    )
    def get_finances_by_year(self, request, project, year):
        """
        Custom action to get finances of a project by year
        Usage: /project-financials/<project_id>/<year>/
        """
        queryFilter = {"project": project, "year": year}
        finance_object = get_object_or_404(ProjectFinancial, **queryFilter)
        return Response(ProjectFinancialSerializer(finance_object).data)


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

    @override
    def list(self, request, *args, **kwargs):
        year = request.query_params.get("year", date.today().year)
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True, context={"finance_year": year})

        return Response(serializer.data)

    @override
    def destroy(self, request, *args, **kwargs):
        """
        Overriding destroy action to get the deleted group id as a response
        """
        group = self.get_object()
        data = group.id
        group.delete()
        return Response({"id": data})

    permission_classes = []
    serializer_class = ProjectGroupSerializer


class ProjectLocationViewSet(BaseViewSet):
    """
    API endpoint that allows Project Locations to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectLocationSerializer

    @override
    def list(self, request, *args, **kwargs):
        year = request.query_params.get("year", date.today().year)
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True, context={"finance_year": year})

        return Response(serializer.data)

    def get_queryset(self):
        """Default is programmer view"""
        return ProjectLocationService.list_all()

    @action(methods=["get"], detail=False, url_path=r"coordinator")
    def list_for_coordinator(self, request):
        """List for coordinator view"""
        year = request.query_params.get("year", date.today().year)
        serializer = ProjectLocationSerializer(
            ProjectLocationService.list_all_for_coordinator(),
            many=True,
            context={
                "finance_year": year,
                "for_coordinator": True,
            },
        )
        return Response(serializer.data)


class ProjectClassViewSet(BaseViewSet):
    """
    API endpoint that allows Project Classes to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectClassSerializer

    @override
    def list(self, request, *args, **kwargs):
        year = request.query_params.get("year", date.today().year)
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True, context={"finance_year": year})

        return Response(serializer.data)

    @override
    def get_queryset(self):
        """Default is programmer view"""
        return (
            ProjectClassService.list_all()
            .select_related("coordinatorClass")
            .prefetch_related("coordinatorClass__finances")
        )

    @action(methods=["get"], detail=False, url_path=r"coordinator")
    def list_for_coordinator(self, request):
        """List for coordinator view"""
        year = request.query_params.get("year", date.today().year)
        serializer = ProjectClassSerializer(
            ProjectClassService.list_all_for_coordinator()
            .prefetch_related("coordinatorClass__finances")
            .select_related("coordinatorClass"),
            many=True,
            context={
                "finance_year": year,
                "for_coordinator": True,
            },
        )
        return Response(serializer.data)

    def is_patch_data_valid(self, data):
        finances = data.get("finances", None)
        if finances == None:
            return False

        parameters = finances.keys()
        if "year" not in parameters:
            return False

        for param in parameters:
            if param == "year":
                continue
            values = finances[param]
            values_length = len(values.keys())

            if type(values) != dict:
                return False
            if values_length == 0 or values_length > 2:
                return False
            if not "frameBudget" in values and not "budgetChange" in values:
                return False

        return True

    @action(
        methods=["patch"],
        detail=False,
        url_path=r"coordinator/(?P<class_id>[0-9a-f]{8}\-[0-9a-f]{4}\-4[0-9a-f]{3}\-[89ab][0-9a-f]{3}\-[0-9a-f]{12})",
    )
    def patch_coordinator_class_finances(self, request, class_id):
        """PATCH endpoint for coordinator classes finances ONLY"""
        if ProjectClassService.instance_exists(
            {"id": class_id, "forCoordinatorOnly": True}
        ):
            finances = request.data.get("finances")
            if self.is_patch_data_valid(request.data):
                startYear = finances.get("year")
                for key in finances.keys():
                    if key != "year":
                        patchData = finances[key]
                        year = ClassFinancialService.get_request_field_to_year_mapping(
                            start_year=startYear
                        ).get(key, None)
                        if year != None:
                            ClassFinancialService.update_or_create(
                                year=year, class_id=class_id, updatedData=patchData
                            )
                        else:
                            return Response(
                                data={"message": "Invalid data format"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                return Response(
                    ProjectClassSerializer(
                        ProjectClassService.get_by_id(id=class_id),
                        context={
                            "finance_year": startYear,
                            "for_coordinator": True,
                        },
                    ).data
                )

            else:
                return Response(
                    data={"message": "Invalid data format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


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
    phase = django_filters.ModelMultipleChoiceFilter(
        field_name="phase",
        queryset=ProjectPhaseSerializer.Meta.model.objects.all(),
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

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.projectWiseService = ProjectWiseService()

    permission_classes = []
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProjectFilter
    serializer_class = ProjectGetSerializer

    @override
    def destroy(self, request, *args, **kwargs):
        """
        Overriding destroy action to get the deleted project id as a response
        """
        project = self.get_object()
        project_id = project.id
        project.delete()
        return Response({"id": project_id})

    @transaction.atomic
    @override
    def partial_update(self, request, *args, **kwargs):
        # finances data appear with field names, convert to year to update
        finances = request.data.pop("finances", None)
        project = self.get_object()
        year = (
            finances.pop("year", date.today().year)
            if finances is not None
            else date.today().year
        )
        if finances is not None:
            fieldToYearMapping = (
                ProjectFinancialService.get_financial_field_to_year_mapping(
                    start_year=year
                )
            )
            for field in finances.keys():
                (
                    projectFinancialObject,
                    created,
                ) = ProjectFinancialService.get_or_create(
                    year=fieldToYearMapping[field], project_id=project.id
                )
                financeSerializer = ProjectFinancialSerializer(
                    projectFinancialObject,
                    data={"value": finances[field]},
                    partial=True,
                    many=False,
                    context={"finance_year": year},
                )
                financeSerializer.is_valid(raise_exception=True)
                financeSerializer.save()

        projectSerializer = self.get_serializer(
            project,
            data=request.data,
            many=False,
            partial=True,
            context={"finance_year": year},
        )
        projectSerializer.is_valid(raise_exception=True)
        updated_project = projectSerializer.save()
        self.projectWiseService.sync_project_to_pw(
            data=request.data, project=updated_project
        )
        return Response(projectSerializer.data)

    @override
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"get_pw_link": True})
        return Response(serializer.data)

    @action(
        methods=["get"],
        detail=False,
        url_path=r"(?P<year>[0-9]{4})",
    )
    def get_projects_by_financial_year(self, request, year):
        """
        Custom action to get projects by financial year
        Usage: /projects/<year>/
        """
        projectQuerySet = self.get_queryset()
        searchPaginator = PageNumberPagination()
        searchPaginator.page_size = 20

        result = searchPaginator.paginate_queryset(projectQuerySet, request)
        serializer = ProjectGetSerializer(
            result, many=True, context={"finance_year": year}
        )
        response = {
            "next": searchPaginator.get_next_link(),
            "previous": searchPaginator.get_previous_link(),
            "count": searchPaginator.page.paginator.count,
            "results": serializer.data,
        }
        return Response(response)

    @action(methods=["get"], detail=True, url_path=r"financials/(?P<year>[0-9]{4})")
    def get_project_with_specific_financial_year(self, request, pk, year):
        """
        Custom action to get a Project with finances from the year specified in url
        """
        try:
            uuid.UUID(str(pk))  # validating UUID
            instance = self.get_object()
            qs = ProjectGetSerializer(
                instance, many=False, context={"finance_year": year}
            ).data
            return Response(qs)
        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        methods=["get"],
        detail=False,
        url_path=r"search-results",
    )
    def get_search_results(self, request):
        """
        Custom action to filter projects by params
        Usage: /projects/search-results/?<filter-params>
        """

        response = {}
        freeSearch = request.query_params.get("freeSearch", None)
        projectGroup = request.query_params.getlist("group", [])
        masterClass = self.request.query_params.getlist("masterClass", [])
        _class = self.request.query_params.getlist("class", [])
        subClass = self.request.query_params.getlist("subClass", [])
        district = self.request.query_params.getlist("district", [])
        division = self.request.query_params.getlist("division", [])
        subDivision = self.request.query_params.getlist("subDivision", [])
        hashTags = request.query_params.getlist("hashtag", [])
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

        if not limit.isnumeric():
            raise ParseError(detail={"limit": "Invalid value"}, code="invalid")
        if limit not in ["10", "20", "30"]:
            raise ValidationError(
                detail={"limit": "Value out of range"}, code="out_of_range"
            )

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
                id__in=queryset.values_list("projectClass", flat=True).distinct(),
                forCoordinatorOnly=False,
            )
        if len(district) > 0 or len(division) > 0 or len(subDivision) > 0:
            projectLocations = ProjectLocation.objects.filter(
                id__in=queryset.values_list("projectLocation", flat=True).distinct(),
                forCoordinatorOnly=False,
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
                chain(groups, queryset, projectClasses, projectLocations)
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
                data={"message": "Invalid value for order"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        searchPaginator = PageNumberPagination()
        searchPaginator.page_size = limit
        result = searchPaginator.paginate_queryset(combinedQuerysets, request)
        serializer = SearchResultSerializer(
            result, many=True, context={"hashtags_include": hashTags}
        )
        response = {
            "next": searchPaginator.get_next_link(),
            "previous": searchPaginator.get_previous_link(),
            "count": searchPaginator.page.paginator.count,
            "results": serializer.data,
        }

        return Response(response)

    @override
    def get_serializer_class(self):
        """
        Overriden ModelViewSet class method to get appropriate serializer depending on the request action
        """
        if self.action in ["list", "retrieve"]:
            return ProjectGetSerializer
        if self.action in ["create", "update", "partial_update"]:
            return ProjectCreateSerializer
        return super().get_serializer_class()

    def get_projects(self, request, for_coordinator=False) -> ProjectGetSerializer:
        queryset = self.filter_queryset(
            self.get_queryset(for_coordinator=for_coordinator)
        )
        financeYear = request.query_params.get("year", None)
        limit = request.query_params.get("limit", None)
        if limit is None:
            querySetCount = queryset.count()
            limit = querySetCount if querySetCount > 0 else 1

        if financeYear is not None and not financeYear.isnumeric():
            raise ParseError(detail={"limit": "Invalid value"}, code="invalid")

        # pagination
        paginator = PageNumberPagination()
        paginator.page_size = limit
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context={
                    "finance_year": financeYear,
                    "for_coordinator": for_coordinator,
                },
            )
            return paginator.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            queryset,
            many=True,
            context={
                "finance_year": financeYear,
                "for_coordinator": for_coordinator,
            },
        )

        return serializer

    @override
    def list(self, request, *args, **kwargs):
        projects = self.get_projects(request, for_coordinator=False)
        return Response(projects.data)

    @action(
        methods=["get"],
        detail=False,
        url_path=r"coordinator",
        serializer_class=ProjectGetSerializer,
    )
    def get_projects_for_coordinator(self, request):
        """
        Custom action to get Projects with coordinator location and classes
        """
        projects = self.get_projects(request, for_coordinator=True)
        return Response(projects.data)

    @override
    def get_queryset(self, for_coordinator=False):
        qs = None
        if for_coordinator == True:
            # add select_related to the queryset to get in the same db query projectClass and projectLocation
            qs = (
                super()
                .get_queryset()
                .select_related(
                    "projectClass",
                    "projectLocation",
                    "projectClass__coordinatorClass",
                    "projectLocation__coordinatorLocation",
                    "projectClass__parent__coordinatorClass",
                    "projectLocation__parent__coordinatorLocation",
                    "projectLocation__parent__parent__coordinatorLocation",
                )
                .filter(
                    Q(projectClass__isnull=False) or Q(projectLocation__isnull=False)
                )
            )
        else:
            qs = super().get_queryset()
        masterClass = self.request.query_params.getlist("masterClass", [])
        _class = self.request.query_params.getlist("class", [])
        subClass = self.request.query_params.getlist("subClass", [])
        collectiveSubLevel = self.request.query_params.getlist("collectiveSubLevel", [])
        otherClassification = self.request.query_params.getlist(
            "otherClassification", []
        )
        subLevelDistrict = self.request.query_params.getlist("subLevelDistrict", [])
        district = self.request.query_params.getlist("district", [])
        division = self.request.query_params.getlist("division", [])
        subDivision = self.request.query_params.getlist("subDivision", [])

        prYearMin = self.request.query_params.get("prYearMin", None)
        overMillion = self.request.query_params.get("overMillion", False)
        prYearMax = self.request.query_params.get("prYearMax", None)
        projects = self.request.query_params.getlist("project", [])
        projectGroups = self.request.query_params.getlist("group", [])
        inGroup = self.request.query_params.get("inGroup", None)
        projectName = self.request.query_params.get("projectName", None)

        # This query param gives the projects which are directly under any given location or class if set to True
        # Else the queryset will also contain the projects containing the child locations/districts
        direct = self.request.query_params.get("direct", False)

        try:
            if projectName is not None:
                qs = qs.filter(name__icontains=projectName)

            if direct in ["true", "True"]:
                direct = True
            elif direct in ["false", "False"]:
                direct = False

            if inGroup is not None:
                if inGroup in ["true", "True"]:
                    qs = qs.filter(projectGroup__isnull=False)
                elif inGroup in ["false", "False"]:
                    qs = qs.filter(projectGroup__isnull=True)

            if overMillion in ["true", "True", True]:
                qs = qs.filter(costForecast__gte=1000)

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
                    has_parent_parent_parent=False,
                    has_parent_parent_parent_parent=False,
                    search_ids=masterClass,
                    model_class=ProjectClass,
                    direct=direct,
                    for_coordinator=for_coordinator,
                )

            if len(_class) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=False,
                    has_parent_parent_parent=False,
                    has_parent_parent_parent_parent=False,
                    search_ids=_class,
                    model_class=ProjectClass,
                    direct=direct,
                    for_coordinator=for_coordinator,
                )

            if len(subClass) > 0:
                subClassModel = ProjectClassService.get_by_id(subClass[0])
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=True,
                    has_parent_parent_parent=False,
                    has_parent_parent_parent_parent=False,
                    search_ids=subClass,
                    model_class=ProjectClass,
                    direct=False
                    if len(subClass) == 1 and "suurpiiri" in subClassModel.name.lower()
                    else direct,
                    for_coordinator=for_coordinator,
                )

            if for_coordinator == True and len(collectiveSubLevel) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=True,
                    has_parent_parent_parent=True,
                    has_parent_parent_parent_parent=False,
                    search_ids=collectiveSubLevel,
                    model_class=ProjectClass,
                    direct=direct,
                    for_coordinator=for_coordinator,
                )

            if for_coordinator == True and len(otherClassification) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=True,
                    has_parent_parent_parent=True,
                    has_parent_parent_parent_parent=True,
                    search_ids=otherClassification,
                    model_class=ProjectClass,
                    direct=direct,
                    for_coordinator=for_coordinator,
                )
            if for_coordinator == True and len(subLevelDistrict) > 0:
                # edit filtering by sublevel district as its parent are not locations but classes
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=True,
                    has_parent_parent_parent=True,
                    has_parent_parent_parent_parent=True,
                    search_ids=subLevelDistrict,
                    model_class=ProjectLocation,
                    direct=direct,
                    for_coordinator=for_coordinator,
                )

            if len(district) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True if for_coordinator == True else False,
                    has_parent_parent=True if for_coordinator == True else False,
                    has_parent_parent_parent=True if for_coordinator == True else False,
                    has_parent_parent_parent_parent=False,
                    search_ids=district,
                    model_class=ProjectLocation,
                    direct=direct,
                    for_coordinator=for_coordinator,
                )
            if for_coordinator == False and len(division) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=False,
                    has_parent_parent_parent=False,
                    has_parent_parent_parent_parent=False,
                    search_ids=division,
                    model_class=ProjectLocation,
                    direct=direct,
                    for_coordinator=for_coordinator,
                )
            if for_coordinator == False and len(subDivision) > 0:
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=True,
                    has_parent_parent_parent=False,
                    has_parent_parent_parent_parent=False,
                    search_ids=subDivision,
                    model_class=ProjectLocation,
                    direct=direct,
                    for_coordinator=for_coordinator,
                )

            return qs
        except Exception as e:
            raise e

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

    @transaction.atomic
    @action(
        methods=["patch"],
        detail=False,
        url_path=r"bulk-update",
        serializer_class=ProjectCreateSerializer,
    )
    def patch_bulk_projects(self, request):
        """
        Custom action to bulk update projects
        Request body format: [{id: project_id, data: {fields to be updated} }, ..]

        """
        try:
            data = json.loads(request.body.decode("utf-8"))
            if self._is_bulk_project_update_data_valid(data):
                projectIds = [projectData["id"] for projectData in data]
                # Building an order by query which makes sure the order is preserved when filtering using __in clause
                preserved = Case(
                    *[When(id=val, then=pos) for pos, val in enumerate(projectIds)],
                    default=len(projectIds),
                )
                qs = self.get_queryset().filter(id__in=projectIds).order_by(preserved)
                financesData = [
                    {
                        "project": projectData["id"],
                        "finances": projectData["data"].pop("finances", None),
                    }
                    for projectData in data
                ]

                for financeData in financesData:
                    finances = financeData.get("finances", None)
                    if finances is not None:
                        year = finances.get("year", date.today().year)
                        if year is None:
                            year = date.today().year
                        fieldToYearMapping = (
                            ProjectFinancialService.get_financial_field_to_year_mapping(
                                start_year=year
                            )
                        )
                        for field in finances.keys():
                            # skip the year field in finances
                            if field == "year":
                                continue
                            (
                                projectFinancialObject,
                                created,
                            ) = ProjectFinancialService.get_or_create(
                                year=fieldToYearMapping[field],
                                project_id=Project(id=financeData["project"]).id,
                            )
                            financeSerializer = ProjectFinancialSerializer(
                                projectFinancialObject,
                                data={"value": finances[field]},
                                partial=True,
                                many=False,
                                context={"finance_year": year},
                            )
                            financeSerializer.is_valid(raise_exception=True)
                            financeSerializer.save()

                serializer = self.get_serializer(
                    qs,
                    data=[
                        {**projectData["data"], "projectId": projectData["id"]}
                        for projectData in data
                    ],
                    many=True,
                    partial=True,
                    context={
                        financeData["project"]: (
                            financeData["finances"].get("year", None)
                            if financeData["finances"] is not None
                            else None
                        )
                        for financeData in financesData
                    },
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(data=serializer.data, status=200)
            else:
                return Response(
                    data={"message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            raise e

    def _is_valid_uuid(self, val):
        try:
            uuid.UUID(str(val))
            return True
        except ValueError:
            return False

    def _is_bulk_project_update_data_valid(self, data):
        if type(data) is list and len(data) > 0:
            for d in data:
                if (
                    "id" in d
                    and self._is_valid_uuid(d["id"])
                    and "data" in d
                    and type(d["id"]) is str
                    and type(d["data"]) is dict
                ):
                    pass
                else:
                    return False
            return True
        else:
            return False

    def _filter_projects_by_hierarchy(
        self,
        qs,
        has_parent: bool,
        has_parent_parent: bool,
        has_parent_parent_parent: bool,
        has_parent_parent_parent_parent: bool,
        search_ids,
        model_class,
        direct=False,
        for_coordinator=False,
    ):
        if direct == True:
            if model_class.__name__ == "ProjectLocation":
                if for_coordinator == True:
                    return qs.filter(
                        projectLocation__coordinatorLocation__in=search_ids
                    )
                return qs.filter(projectLocation__in=search_ids)
            elif model_class.__name__ == "ProjectClass":
                if for_coordinator == True:
                    return qs.filter(projectClass__coordinatorClass__in=search_ids)
                return qs.filter(
                    projectClass__in=search_ids, projectLocation__isnull=True
                )
        paths = []
        if for_coordinator == True and model_class.__name__ == "ProjectLocation":
            paths = (
                model_class.objects.filter(
                    id__in=search_ids,
                    parentClass__isnull=not has_parent,
                    parentClass__parent__isnull=not has_parent_parent,
                    parentClass__parent__parent__isnull=not has_parent_parent_parent,
                    parentClass__parent__parent__parent__isnull=not has_parent_parent_parent_parent,
                    forCoordinatorOnly=for_coordinator,
                )
                .distinct()
                .values_list("path", flat=True)
            )
        else:
            paths = (
                model_class.objects.filter(
                    id__in=search_ids,
                    parent__isnull=not has_parent,
                    parent__parent__isnull=not has_parent_parent,
                    parent__parent__parent__isnull=not has_parent_parent_parent,
                    parent__parent__parent__parent__isnull=not has_parent_parent_parent_parent,
                    forCoordinatorOnly=for_coordinator,
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
            if for_coordinator == True:
                return qs.filter(projectLocation__coordinatorLocation__in=ids)
            return qs.filter(projectLocation__in=ids)
        elif model_class.__name__ == "ProjectClass":
            if for_coordinator == True:
                return qs.filter(projectClass__coordinatorClass__in=ids)
            return qs.filter(projectClass__in=ids)

    def _filter_projects_by_programming_year(self, qs, prYearMin, prYearMax):
        currYear = datetime.date.today().year

        if prYearMin is not None and prYearMax is not None:
            if not prYearMax.isnumeric():
                raise ParseError(detail={"prYearMax": "Invalid value"}, code="invalid")
            if not prYearMin.isnumeric():
                raise ParseError(detail={"prYearMin": "Invalid value"}, code="invalid")

            prYearMin = int(prYearMin)
            prYearMax = int(prYearMax)
            if prYearMin > prYearMax:
                raise ValidationError(
                    detail={"prYearMin": "prYearMin cannot be greater than prYearMax"},
                    code="prYearMin_gt_prYearMax",
                )

            financialProjectIds = (
                ProjectFinancialService.find_by_min_value_and_year_range(
                    min_value=0, year_range=range(prYearMin, prYearMax + 1)
                )
                .values_list("project", flat=True)
                .distinct()
            )
            qs = qs.filter(Q(id__in=financialProjectIds) & Q(programmed=True))

        elif prYearMin is not None:
            if not prYearMin.isnumeric():
                raise ParseError(detail={"prYearMin": "Invalid value"}, code="invalid")

            prYearMin = int(prYearMin)
            financialProjectIds = (
                ProjectFinancialService.find_by_min_value_and_min_year(
                    min_value=0, min_year=prYearMin
                )
                .values_list("project", flat=True)
                .distinct()
            )
            qs = qs.filter(Q(id__in=financialProjectIds) & Q(programmed=True))

        elif prYearMax is not None:
            if not prYearMax.isnumeric():
                raise ParseError(detail={"prYearMax": "Invalid value"}, code="invalid")
            prYearMax = int(prYearMax)

            financialProjectIds = (
                ProjectFinancialService.find_by_min_value_and_max_year(
                    min_value=0, max_year=prYearMax
                )
                .values_list("project", flat=True)
                .distinct()
            )
            qs = qs.filter(Q(id__in=financialProjectIds) & Q(programmed=True))

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


def stream_data():
    while True:
        time.sleep(1)
        yield "Signal"


class StreamView(APIView):
    def get(self, request, format=None):
        """
        Return a stream response on signal change
        """
        stream_generator = stream_data()
        response = StreamingHttpResponse(
            stream_generator, status=200, content_type="text/event-stream"
        )
        return response


class ClassFinancialViewSet(BaseViewSet):
    """
    API endpoint that allows Class Financials to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ClassFinancialSerializer
