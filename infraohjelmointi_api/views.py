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
        Custom action to get finances of a project for an year.

            URL Parameters
            ----------

            project_id : UUID string
            year : Int

            Usage
            ----------

            project-financials/<project_id>/<year>

            Returns
            -------

            JSON
                ProjectFinancial instance for the given year and project id
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
        """
        Overriden list action to get custom response for a GET request to hashtags endpoint

            Usage
            ----------

            project-hashtags/

            Returns
            -------

            List of ProjectHashtag and top 15 most used hash tags

            JSON
                { "hashTags": [ProjectHashTag], "popularHashTags": [ProjectHashTag] }
        """
        qs = self.get_queryset().prefetch_related("relatedProject")
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

    serializer_class = ProjectGroupSerializer

    @override
    def list(self, request, *args, **kwargs):
        """
        Overriden list action to get a list of ProjectGroup

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Groups with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-groups/?year=<year>

            Returns
            -------

            JSON
                List of ProjectGroup instances with financial sums for projects under each group
        """
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

    @action(
        methods=["get"],
        detail=False,
        url_path=r"coordinator",
    )
    def get_groups_for_coordinator(self, request):
        """
        Custom action to get ProjectGroup instances with coordinator location/classes

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Groups with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-groups/coordinator/?year=<year>

            Returns
            -------

            JSON
                List of ProjectGroup instances with financial sums for projects under each group
        """
        year = request.query_params.get("year", date.today().year)
        qs = self.get_queryset().select_related(
            "classRelation",
            "locationRelation",
            "classRelation__coordinatorClass",
            "locationRelation__coordinatorLocation",
            "classRelation__parent__coordinatorClass",
            "locationRelation__parent__coordinatorLocation",
            "locationRelation__parent__parent__coordinatorLocation",
        )
        serializer = self.get_serializer(
            qs, many=True, context={"finance_year": year, "for_coordinator": True}
        )
        return Response(serializer.data)

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
        """
        Overriden list action to get a list of ProjectLocation

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Locations with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-locations/?year=<year>

            Returns
            -------

            JSON
                List of ProjectLocation instances with financial sums for projects under each location
        """
        year = request.query_params.get("year", date.today().year)
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True, context={"finance_year": year})

        return Response(serializer.data)

    def get_queryset(self):
        """Default is programmer view"""
        return ProjectLocationService.list_all()

    @action(methods=["get"], detail=False, url_path=r"coordinator")
    def list_for_coordinator(self, request):
        """
        Overriden list action to get a list of coordinator ProjectLocations

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Locations with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-locations/coordinator/?year=<year>

            Returns
            -------

            JSON
                List of ProjectLocation instances with financial sums for projects under each location
        """
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
        """
        Overriden list action to get a list of ProjectClass

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Class with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-classes/?year=<year>

            Returns
            -------

            JSON
                List of ProjectClass instances with financial sums for projects under each class
        """
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
        """
        Overriden list action to get a list of coordinator ProjectClass

            URL Query Parameters
            ----------

            year (optional) : Int

            Year number to fetch Project Class with finances starting from this year.
            Defaults to current year.

            Usage
            ----------

            project-classes/?year=<year>

            Returns
            -------

            JSON
                List of ProjectClass instances with financial sums for projects under each class
        """
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
        """
        Utility function to validate patch data sent to the custom PATCH endpoint for coordinator class finances
        """
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
        """
        Custom PATCH endpoint for coordinator classes **finances ONLY**

            URL Parameters
            ----------

            class_id : UUID string

            Coordinator class Id

            Usage
            ----------

            project-classes/coordinator/<class_id>/

            Returns
            -------

            JSON
                Patched coordinator ProjectClass Instance
        """
        if not ProjectClassService.instance_exists(
            id=class_id, forCoordinatorOnly=True
        ):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not self.is_patch_data_valid(request.data):
            return Response(
                data={"message": "Invalid data format"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        finances = request.data.get("finances")
        startYear = finances.get("year")
        for parameter in finances.keys():
            if parameter == "year":
                continue
            patchData = finances[parameter]
            year = ClassFinancialService.get_request_field_to_year_mapping(
                start_year=startYear
            ).get(parameter, None)

            if year == None:
                return Response(
                    data={"message": "Invalid data format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        ClassFinancialService.update_or_create(
            year=year, class_id=class_id, updatedData=patchData
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
        """
        Overriden partial_update (PATCH) action to accomodate ProjectFinancial update from this endpoint

            Usage
            ----------

            projects/<project_id>/

            Returns
            -------

            JSON
                Patched Project Instance
        """
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
        Custom action to get projects with financials starting from the year provided

            URL Parameters
            ----------

            year : int

            Starting year for financials

            Usage
            ----------

            projects/<year>/

            Returns
            -------

            JSON
                List of projects with finances starting from the year provided
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
        Custom action to get a project with financials starting from the year provided

            URL Parameters
            ----------

            project_id : UUID string

            year : int

            Usage
            ----------

            projects/<project_id>/financials/<year>/

            Returns
            -------

            JSON
                Project instance with finances starting from the year provided
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
        Custom action to get filtered project related results. Response contains filtered projects and class,location, groups instances.

            URL Query Parameters (All Optional)
            ----------

            freeSearch : string

            Searches the provided string against project, groups and hashtag names and returns 3 lists.\n
            Defaults to empty lists if query param is empty.\n
            Usage: projects/search-results/?freeSearch=<string>


            group: UUID

            Filters the groups in response with the ids provided. Multiple group ids can be provided with the query.\n
            Usage: projects/search-results/?group=<uuid>&group=<uuid>

            masterClass : UUID

            Filters the projects related to the masterClass ids provided. Also responds with the masterClass instances.\n
            Usage: projects/search-results/?masterClass=<uuid>&masterClass=<uuid>

            class : UUID

            Filters the projects related to the Class ids provided. Also responds with the Class instances.\n
            Usage: projects/search-results/?class=<uuid>&class=<uuid>

            subclass : UUID

            Filters the projects related to the subClass ids provided. Also responds with the subClass instances.\n
            Usage: projects/search-results/?subClass=<uuid>&subClass=<uuid>

            district : UUID

            Filters the projects related to the district ids provided. Also responds with the district instances.\n
            Usage: projects/search-results/?district=<uuid>&district=<uuid>

            division : UUID

            Filters the projects related to the division ids provided. Also responds with the division instances.\n
            Usage: projects/search-results/?division=<uuid>&division=<uuid>

            subDivision : UUID

            Filters the projects related to the subDivision ids provided. Also responds with the subDivision instances.\n
            Usage: projects/search-results/?subDivision=<uuid>&subDivision=<uuid>

            hashtag : UUID

            Hashtag ids provided here are used to filter the hashtags related to the project instances in response.\n
            Only the hashtag ids provided using this query param are allowed in response if provided.\n
            Usage: projects/search-results/?hashtag=<uuid>&hashtag=<uuid>

            order : string [new | old | project | group | phase]

            Orders the instances in response according to the query param.
            Usage: projects/search-results/?order=<string>

            prYearMin : int

            Filters projects by minimum programming year.\n
            Projects with finances > 0 starting from the year provided are returned.\n
            Usage: projects/search-results/?prYearMin=<int>

            prYearMax : int

            Filters projects by maximum programming year.\n
            Projects with finances > 0 and before the provided year are returned.\n
            Usage: projects/search-results/?prYearMax=<int>

            inGroup : bool

            Filters projects by if they belong to a group or not.\n
            Usage: projects/search-results/?inGroup=<bool>

            projectName : string

            Filters project name by string provided.\n
            Usage: projects/search-results/?projectName=<string>

            limit : int [10 | 20 | 30]

            Limits the number of results in response and enables paginates the rest.\n
            Defaults to 10.
            Usage: projects/search-results/?limit=<int>

            Usage
            ----------

            projects/search-results/?<query_params>

            Returns
            -------
            List of mixed instances, ProjectGroup, ProjectClass, ProjectLocation, Project
            JSON
                [{
                name: <name of instance>,
                id: <uuid>,
                type: <type of instance>,
                hashtags: [] <list of hashtags associated with the Project instance>,
                phase: <ProjectPhase instance linked to the Project instance>,
                path: <Class and location path under which a Project instance falls>,
                programmed: <Boolean value stating if a Project instance is programmed>
                }]\n

                IF freeSearch in query params\n
                {
                    "projects": <list of project instances>,
                    "hashtags": <list of hashtag instances>,
                    "groups": <list of group instances>,
                }
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
        """
        Utility function to get a filtered project queryset

            Parameters
            ----------

            request : HttpRequest
            request object

            for_coordinator : Bool
            Paramter stating if the projects are needed for coordinator

            Returns
            -------

            Project Queryset
        """
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
        """
        Overriden list action for projects to make use of the utility function and get projects for planning by default.\n
        All search result url query paramters can be used to filter projects here.
        """
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
        Custom action to get Projects with coordinator location and classes.\n
        All search result url query paramters can be used to filter projects here.
        """
        projects = self.get_projects(request, for_coordinator=True)
        return Response(projects.data)

    @override
    def get_queryset(self, for_coordinator=False):
        """
        Overriden the default get_queryset method to apply filtering by URL query params.\n
        Provided url query params filter out the queryset before returning it.
        """
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
                    Q(projectClass__isnull=False) | Q(projectLocation__isnull=False)
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
                qs = self._filter_projects_by_hierarchy(
                    qs=qs,
                    has_parent=True,
                    has_parent_parent=True,
                    has_parent_parent_parent=True,
                    has_parent_parent_parent_parent=True,
                    search_ids=subLevelDistrict,
                    model_class=ProjectLocation,
                    direct=for_coordinator,
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
                    direct=direct if for_coordinator == False else for_coordinator,
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
        Custom action to get notes related to a project

            URL Parameters
            ----------

            project_id : UUID string

            Usage
            ----------

            projects/<project_id>/notes/

            Returns
            -------

            JSON
                List of ProjectNote instances
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
        Custom action to get allow bulk project updates in one PATCH request

            Usage
            ----------

            projects/bulk-update/
            Request body format: [{id: project_id, data: {fields to be updated} }, ..]

            Returns
            -------

            JSON
                List of updated Project instances
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
        """
        Utility function to filter the provided Project queryset by the model_class instance and other paramters provided.\n
        Hierarchy includes location or class.

            Parameters
            ----------

            qs : Project Queryset

            model_class : ProjectLocation | ProjectClass

            The type of hierarchy being used to filter projects.

            search_ids : list[UUID]

            list of ids belonging to the model_class

            has_parent : bool
            has_parent_parent : bool
            has_parent_parent_parent : bool
            has_parent_parent_parent_parent : bool

            Constraint parameters used to enforce that the search_ids have a parent instance or not.\n
            Used to differentiate between masterClass/class/subClass/collectiveSubLevel or district/division/subDivision

            direct : bool

            True if projects must be directly under the provided search_ids, else projects under child class/locations of search_ids will also be included.\n
            Defaults to False

            for_coordinator : bool

            search_ids provided belong to coordinator or not. Defaults to False.

            Returns
            -------

            Queryset
                Filtered Project Queryset
        """
        # All coordinator locations are fetched with direct=True since only districts exist in coordinator view without any further location children
        if direct == True:
            if model_class.__name__ == "ProjectLocation":
                if for_coordinator == True:
                    return qs.filter(
                        Q(projectLocation__coordinatorLocation__in=search_ids)
                        | Q(projectLocation__parent__coordinatorLocation__in=search_ids)
                        | Q(
                            projectLocation__parent__parent__coordinatorLocation__in=search_ids
                        )
                    )
                return qs.filter(projectLocation__in=search_ids)
            elif model_class.__name__ == "ProjectClass":
                if for_coordinator == True:
                    return qs.filter(projectClass__coordinatorClass__in=search_ids)
                return qs.filter(
                    projectClass__in=search_ids, projectLocation__isnull=True
                )
        paths = []

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
                Q(*[("path__startswith", path) for path in paths], _connector=Q.OR),
                forCoordinatorOnly=for_coordinator,
            )
            .distinct()
            .values_list("id", flat=True)
            if len(paths) > 0
            else []
        )

        if model_class.__name__ == "ProjectLocation":
            return qs.filter(projectLocation__in=ids)
        elif model_class.__name__ == "ProjectClass":
            if for_coordinator == True:
                return qs.filter(projectClass__coordinatorClass__in=ids)
            return qs.filter(projectClass__in=ids)

    def _filter_projects_by_programming_year(self, qs, prYearMin, prYearMax):
        """
        Utility function to filter Project Queryset by financial years.\n

            Parameters
            ----------

            qs : Project Queryset

            prYearMin : int

            Used to filter for projects with financials starting from prYearMin and financials value > 0.

            prYearMax : int

            Used to filter for projects with financials before prYearMax and financials value > 0.

            Returns
            -------

            Queryset
                Filtered Project Queryset
        """

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
        if self.action in ["list", "retrieve"]:
            return NoteGetSerializer
        if self.action == "create":
            return NoteCreateSerializer
        return NoteUpdateSerializer

    @action(methods=["get"], detail=True, url_path=r"history")
    def history(self, request, pk):
        """
        Custom action to get edit history of a note

            URL Parameters
            ----------

            note_id : UUID string

            Usage
            ----------

            notes/<note_id>/history/

            Returns
            -------

            JSON
                List of ProjectNote instances
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
        Custom action to get edit history of a note edited by a specific user
            URL Parameters
            ----------

            note_id : UUID string

            user_id : UUID string

            Usage
            ----------

            notes/<note_id>/history/<user_id>/

            Returns
            -------

            JSON
                List of ProjectNote instances
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
