from datetime import date, timedelta, datetime
import datetime as dt_module
import logging
from django_filters.rest_framework import DjangoFilterBackend
import django_filters
from infraohjelmointi_api.serializers import (
    AppStateValueSerializer,
    ProjectHashtagSerializer,
    ProjectPhaseSerializer,
    ProjectGetSerializer,
    ProjectCreateSerializer,
    ProjectFinancialSerializer,
    ProjectGroupSerializer,
    ProjectWithFinancesSerializer,
    SearchResultSerializer,
    ProjectNoteGetSerializer,
)
from infraohjelmointi_api.models import (
    AuditLog,
    ClassFinancial,
    LocationFinancial,
    Project,
    ProjectGroup,
    ProjectClass,
    ProjectLocation,
    ProjectFinancial,
    User,
)
from infraohjelmointi_api.services import (
    AppStateValueService,
    ProjectPhaseService,
    ProjectWiseService,
    ProjectFinancialService,
    ProjectClassService,
)
from infraohjelmointi_api.services.utils import create_comprehensive_project_data
import json

from infraohjelmointi_api.services.SapCurrentYearService import SapCurrentYearService
from .BaseViewSet import BaseViewSet
from distutils.util import strtobool
from ..paginations import StandardResultsSetPagination
from overrides import override
from rest_framework.response import Response
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.pagination import PageNumberPagination
import uuid
from rest_framework import status
from itertools import chain
from django.db.models import Count, Case, When, Q, F
from django.db.models.signals import post_save
from collections import defaultdict
from dateutil.relativedelta import relativedelta

logger = logging.getLogger("infraohjelmointi_api")


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
            "personConstruction": ["exact"],
        }
        model = Project


class ProjectViewSet(BaseViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.projectWiseService = ProjectWiseService()

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
        old_project_values = {field: str(getattr(project, field)) for field in project.__dict__ if not field.startswith('_')}
        project_id = project.id
        project.delete()
        self.audit_log_project_card_changes(
            old_project_values,
            {},
            None,
            request.user,
            request.build_absolute_uri(),
            "DELETE"
        )
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

        # chcking if request contains any data changes that needs to be audit logged
        # and getting the previous values from the project object before it changes
        audit_loggable_fields = [
            "category",
            "projectClass",
            "name",
            "phase",
            "constructionPhaseDetail",
            "planningStartYear",
            "constructionEndYear",
            "estPlanningStart",
            "estPlanningEnd",
            "estConstructionStart",
            "estConstructionEnd",
            "estWarrantyPhaseStart",
            "estWarrantyPhaseEnd",
            "presenceStart",
            "presenceEnd",
            "visibilityStart",
            "visibilityEnd",
        ]
        old_values_for_audit_log = {
            field: (
                str(getattr(getattr(project, field), 'id', None))
                if hasattr(getattr(project, field), 'id')
                else str(getattr(project, field))
            )
            for field in audit_loggable_fields
            if field in request.data
        }

        year = (
            finances.pop("year", date.today().year)
            if finances is not None
            else date.today().year
        )
        forced_to_frame = (
            finances.pop("forcedToFrame", False) if finances is not None else False
        )

        forced_to_frame_status, _ = AppStateValueService.get_or_create_by_name(name="forcedToFrameStatus")

        if forced_to_frame_status.value and forced_to_frame is False:
            if 'estPlanningStart' in request.data:
                request.data['frameEstPlanningStart'] = request.data['estPlanningStart']
            if 'estPlanningEnd' in request.data:
                request.data['frameEstPlanningEnd'] = request.data['estPlanningEnd']
            if 'estConstructionStart' in request.data:
                request.data['frameEstConstructionStart'] = request.data['estConstructionStart']
            if 'estConstructionEnd' in request.data:
                request.data['frameEstConstructionEnd'] = request.data['estConstructionEnd']
            if 'estWarrantyPhaseStart' in request.data:
                request.data['frameEstWarrantyPhaseStart'] = request.data['estWarrantyPhaseStart']
            if 'estWarrantyPhaseEnd' in request.data:
                request.data['frameEstWarrantyPhaseEnd'] = request.data['estWarrantyPhaseEnd']

        if finances is not None:
            finance_instances = self.create_updated_finance_instances(finances, project, forced_to_frame, year)
            # saving old/previous values for audit log
            old_finance_values = ProjectFinancialService.find_by_project_id_and_finance_years(
                project_id=project.id,
                finance_years=[instance.year for instance in finance_instances],
                for_frame_view=forced_to_frame
            )
            old_finance_values = {obj.year: str(obj.value) for obj in old_finance_values}
            if len(finance_instances) > 0:
                updated_finance_instance = ProjectFinancialService.update_or_create_bulk(
                    project_financials=finance_instances
                )
                new_finance_values = {obj.year: obj.value for obj in updated_finance_instance}
                self.audit_log_project_card_changes(
                    old_finance_values,
                    new_finance_values,
                    project,
                    request.user,
                    request.build_absolute_uri(),
                    "UPDATE"
                )
                updated_finance_instance = updated_finance_instance[0]
                if forced_to_frame_status.value and forced_to_frame is False:
                    existing_frame_view_map = defaultdict(dict)
                    frame_view_finances = ProjectFinancial.objects.filter(forFrameView=True, project_id=project.id)

                    for finance in frame_view_finances:
                        existing_frame_view_map[(finance.project_id, finance.year)] = finance

                    new_finances = []
                    update_finances = []

                    for finance in finance_instances:
                        key = (finance.project_id, finance.year)
                        if key in existing_frame_view_map:
                            # Update existing frame-view entry
                            frame_view_finance = existing_frame_view_map[key]
                            frame_view_finance.value = finance.value
                            update_finances.append(frame_view_finance)
                        else:
                            # Create new frame-view entry
                            new_finance = ProjectFinancial(
                                project_id=finance.project_id,
                                year=finance.year,
                                value=finance.value,
                                forFrameView=True
                            )
                            new_finances.append(new_finance)

                    ProjectFinancialService.update_or_create_bulk(project_financials=new_finances)

                    if update_finances:
                        ProjectFinancialService.update_or_create_bulk(project_financials=update_finances)
                # adding finance_year here so that on save the instance that gets to the post_save signal has this value on finance_update
                updated_finance_instance.finance_year = year
                post_save.send(
                    ProjectFinancial, instance=updated_finance_instance, created=False
                )
        # adding forcedToFrame here so that on save the instance that gets to the post_save signal has this value
        project.forcedToFrame = forced_to_frame
        # adding finance_year here so that on save the instance that gets to the post_save signal has this value
        project.finance_year = year


        # when project is moved to warrantyPeriod, we need to automatically set warranty phase end and start dates so that warranty period
        # lasts two years from construction end if no warranty period dates aren't already set for the project
        phase_from_data = request.data.get('phase')
        if phase_from_data:
            phase = ProjectPhaseService.get_by_id(phase_from_data)
            if phase.value == 'warrantyPeriod':
                project_warranty_phase_start = request.data.get('estWarrantyPhaseStart') or project.estWarrantyPhaseStart
                project_has_warranty_phase_end = request.data.get('estWarrantyPhaseEnd') or project.estWarrantyPhaseEnd
                if project_warranty_phase_start is None:
                    est_construction_end = request.data.get('estConstructionEnd') or project.estConstructionEnd
                    project_warranty_phase_start = self.parse_date(est_construction_end) + timedelta(days=1)
                    request.data['estWarrantyPhaseStart'] = project_warranty_phase_start.isoformat()
                if project_has_warranty_phase_end is None:
                    project_has_warranty_phase_end = self.parse_date(project_warranty_phase_start) + relativedelta(years=2)
                    request.data['estWarrantyPhaseEnd'] = project_has_warranty_phase_end.isoformat()

        project_serializer = self.get_serializer(
            project,
            data=request.data,
            many=False,
            partial=True,
            context={"finance_year": year, "forcedToFrame": forced_to_frame},
        )
        project_serializer.is_valid(raise_exception=True)
        updated_project = project_serializer.save()

        # saving audit logs after project data was changed
        if (old_values_for_audit_log):
            new_values_for_audit_log = {field: request.data[field] for field in audit_loggable_fields if field in request.data}
            self.audit_log_project_card_changes(
                old_values_for_audit_log,
                new_values_for_audit_log,
                updated_project,
                request.user,
                request.build_absolute_uri(),
                "UPDATE"
            )

        # updating changed data to ProjectWise
        self._sync_project_to_projectwise(request.data, project, updated_project)
        return Response(project_serializer.data)

    def parse_date(self, date):
        if isinstance(date, str):
            return datetime.strptime(date, '%d.%m.%Y').date()
        return date

    def audit_log_project_card_changes(self, old_values, new_values, project, user, url, operation):
        audit_log = AuditLog(
            actor=user if isinstance(user, User) else None,
            operation=operation,
            log_level="INFO",
            origin='infrahankkeiden_ohjelmointi',
            status='SUCCESS',
            project=project,
            old_values=old_values,
            new_values=new_values,
            endpoint=url,
        )
        audit_log.save()

    def create_updated_finance_instances(self, finances, project, forced_to_frame, year):
        finance_instances = []
        for field in finances.keys():
                if hasattr(project, "lock"):
                    raise ValidationError(
                        detail={
                            field: "The field {} cannot be modified when the project is locked".format(
                                field
                            )
                        },
                        code="project_locked",
                    )

                finance_year = ProjectFinancialService.convert_financial_field_to_year(field, year)
                finance_instance = ProjectFinancial(
                    project=project,
                    value=finances[field],
                    year=finance_year,
                    forFrameView=forced_to_frame,
                )

                finance_instances.append(finance_instance)

        return finance_instances

    @override
    def retrieve(self, request, *args, **kwargs):
        """
        Overriden retrieve action to get PW link with a single project and allow frame view financials retrieval.\n

            URL Query Parameters
            ----------

            project_id : UUID string

            forcedToFrame (optional) : Bool

            Query parameter to state if project returned should contain frame view financial values.
            Defaults to False.

            Usage
            ----------

            projects/<project_id>/?forcedToFrame=<bool>

            Returns
            -------

            JSON
                Project instance with financial values.
        """
        instance = self.get_object()
        forcedToFrame = request.query_params.get("forcedToFrame", False)
        if forcedToFrame in ["False", "false"]:
            forcedToFrame = False

        if forcedToFrame in ["true", "True"]:
            forcedToFrame = True

        if forcedToFrame not in [True, False]:
            raise ParseError(
                detail={"forcedToFrame": "Value must be a boolean"}, code="invalid"
            )
        serializer = self.get_serializer(
            instance, context={"get_pw_link": True, "forcedToFrame": forcedToFrame}
        )
        return Response(serializer.data)

    @action(
        methods=["get"],
        detail=False,
        url_path=r"(?P<year>[0-9]{4})",
        name="get_projects_by_financial_year",
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

    @action(
        methods=["get"],
        detail=True,
        url_path=r"financials/(?P<year>[0-9]{4})",
        name="get_project_by_financial_year",
    )
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
        name="get_search_results",
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
            groups = ProjectGroup.objects.filter(name__in=projectGroup).select_related("classRelation")

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

    def get_projects(
        self, request, for_coordinator=False, forFrameView=False
    ) -> ProjectGetSerializer:
        """
        Utility function to get a filtered project queryset

            Parameters
            ----------

            request : HttpRequest
            request object

            for_coordinator : Bool
            Paramter stating if the projects are needed for coordinator

            forFrameView : Bool
            Paramter to identify if projects being returned should have frame view finances.

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
            logger.error(f"{request.user.id}: Invalid financeYear provided: {financeYear}")
            raise ParseError(detail={f"{request.user.id}: limit": "Invalid value"}, code="invalid")

        # pagination
        paginator = PageNumberPagination()
        paginator.page_size = limit
        page = paginator.paginate_queryset(queryset, request)

        year = date.today().year if financeYear == None else int(financeYear)
        finances = ProjectFinancialSerializer(
            ProjectFinancial.objects.filter(
                forFrameView=forFrameView,
                year__in=range(year, year + 11)
            ),
            many=True,
            context={"discard_FK": False}
        ).data

        projects_to_finances = defaultdict(list)
        for f in finances:
            projects_to_finances[f["project"]].append(f)

        current_year = dt_module.datetime.now().year
        sap_values = SapCurrentYearService.get_by_year(current_year)
        projects_to_sap_values = defaultdict(list)
        for sap_value in sap_values:
            # Append the SAP value to the list of SAP values for the corresponding project_id
            projects_to_sap_values[sap_value.project_id].append(sap_value)

        serializerContext = {
            "finance_year": financeYear,
            "for_coordinator": for_coordinator,
            "forcedToFrame": forFrameView,
            "projects_to_finances": projects_to_finances,
            "sap_values_by_project": projects_to_sap_values
        }

        if page is not None:
            serializer = self.get_serializer(
                page,
                many=True,
                context=serializerContext,
            )
            serializer_data = serializer.data
            return paginator.get_paginated_response(serializer_data)

        serializer = self.get_serializer(
            queryset,
            many=True,
            context=serializerContext,
        )

        return serializer

    @override
    def list(self, request, *args, **kwargs):
        """
        Overriden list action for projects to make use of the utility function and get projects for planning by default.\n
        All search result url query paramters can be used to filter projects here.
        """

        projects = self.get_projects(request, for_coordinator=False, forFrameView=False)
        return Response(projects.data)

    @action(
        methods=["get"],
        detail=False,
        url_path=r"coordinator",
        serializer_class=ProjectGetSerializer,
        name="get_coordinator_projects",
    )
    def get_projects_for_coordinator(self, request):
        """
        Custom action to get Projects with coordinator location and classes.\n
        All search result url query paramters can be used to filter projects here.

            URL Query Parameters
            ----------

            forcedToFrame (optional) : Bool

            Query parameter to state if projects returned should contain frame view financial values.
            Defaults to False.

            Usage
            ----------

            projects/coordinator/?forcedToFrame=<bool>

            Returns
            -------

            JSON
                List of Project Instances with coordinator class/locations and normal/frameView financial values.
        """
        forcedToFrame = request.query_params.get("forcedToFrame", False)
        if forcedToFrame in ["False", "false"]:
            forcedToFrame = False

        if forcedToFrame in ["true", "True"]:
            forcedToFrame = True

        if forcedToFrame not in [True, False]:
            raise ParseError(
                detail={"forcedToFrame": "Value must be a boolean"}, code="invalid"
            )

        projects = self.get_projects(
            request, for_coordinator=True, forFrameView=forcedToFrame
        )
        return Response(projects.data)

    @override
    def get_queryset(self, for_coordinator=False):
        """
        Overriden the default get_queryset method to apply filtering by URL query params.\n
        Provided url query params filter out the queryset before returning it.
        """
        qs = None
        year = int(self.request.query_params.get("year", date.today().year))
        if for_coordinator == True:
            # add select_related to the queryset to get in the same db query projectClass and projectLocation
            qs = (
                super()
                .get_queryset()
                .select_related(
                    "projectClass",
                    "projectLocation",
                    "lock",
                    "phase",
                    "category",
                    "personPlanning",
                    "personConstruction",
                    "personProgramming",
                    "personConstruction",
                    "budgetOverrunReason",
                    "projectClass__coordinatorClass",
                    "projectLocation__coordinatorLocation",
                    "projectClass__parent__coordinatorClass",
                    "projectLocation__parent__coordinatorLocation",
                    "projectLocation__parent__parent__coordinatorLocation",
                )
                .prefetch_related(
                    "favPersons",
                    "hashTags",
                )
                .filter(
                    Q(projectClass__isnull=False) | Q(projectLocation__isnull=False)
                )
            )
        else:
            qs = (
                super()
                .get_queryset()
                .select_related(
                    "projectClass",
                    "projectLocation",
                    "lock",
                    "phase",
                    "category",
                    "personPlanning",
                    "personConstruction",
                    "personProgramming",
                    "personConstruction",
                    "budgetOverrunReason",
                )
                .prefetch_related(
                    "favPersons",
                    "hashTags",
                )
            )
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

        project_districts = self.request.query_params.getlist("projectdistrict", [])
        project_divisions = self.request.query_params.getlist("projectdivision", [])
        project_sub_divisions = self.request.query_params.getlist("projectsubDivision", [])

        prYearMin = self.request.query_params.get("prYearMin", None)
        overMillion = self.request.query_params.get("overMillion", False)
        prYearMax = self.request.query_params.get("prYearMax", None)
        projects = self.request.query_params.getlist("project", [])
        inGroup = self.request.query_params.get("inGroup", None)
        project_name = self.request.query_params.getlist("projectName", [])
        hash_tags = self.request.query_params.getlist("hashtag", [])
        project_group = self.request.query_params.getlist("group", [])

        # This query param gives the projects which are directly under any given location or class if set to True
        # Else the queryset will also contain the projects containing the child locations/districts
        direct = self.request.query_params.get("direct", False)

        try:
            q_objects = Q()

            if len(project_name) > 0 or len(project_group) > 0:
                q_objects |= Q(name__in=project_name)
                q_objects |= Q(projectGroup__name__in=project_group)

            if len(hash_tags) > 0:
                q_objects |= Q(hashTags__id__in=hash_tags)

            qs = qs.filter(q_objects)

            if len(project_sub_divisions) > 0:
                qs = qs.filter(projectDistrict__in=project_sub_divisions)

            elif len(project_divisions) > 0:
                qs = qs.filter(
                    Q(projectDistrict__in=project_divisions) |
                    Q(projectDistrict__parent__in=project_divisions)
                )

            elif len(project_districts) > 0:
                qs = qs.filter(
                    Q(projectDistrict__in=project_districts) |
                    Q(projectDistrict__parent__in=project_districts) |
                    Q(projectDistrict__parent__parent__in=project_districts)
                )

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

    @action(methods=["get"], detail=True, url_path=r"notes", name="get_project_notes")
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
        url_path=r"bulk-update/forced-to-frame",
        serializer_class=ProjectWithFinancesSerializer,
        name="patch_bulk_forced_to_frame",
    )
    def patch_bulk_forced_to_frame(self, request):
        """
        Custom action to get allow bulk forced to frame project updates in one PATCH request

            Usage
            ----------

            projects/bulk-update/forced-to-frame
            Request body format: [{id: project_id, data: {} }, ..]

            Returns
            -------

            JSON
                List of updated Project instances
        """

        def batch_process(queryset, batch_size):
            total = len(queryset)
            for start in range(0, total, batch_size):
                end = min(start + batch_size, total)
                yield queryset[start:end]

        bulk_size = 100

        new_project_finances, update_project_finances = self.update_forced_to_frame_projects()

        # Bulk create new ProjectFinancial entries
        ProjectFinancial.objects.bulk_create(new_project_finances, bulk_size)

        # Bulk update existing ProjectFinancial entries
        if update_project_finances:
            for batch in batch_process(update_project_finances, bulk_size):
                ProjectFinancial.objects.bulk_update(batch, ['value'])

        new_class_finances, update_class_finances = self.update_forced_to_frame_classes()

        # Bulk create new ClassFinancial entries
        ClassFinancial.objects.bulk_create(new_class_finances, bulk_size)

        # Bulk update existing ClassFinancial entries
        if update_class_finances:
            for batch in batch_process(update_class_finances, bulk_size):
                ClassFinancial.objects.bulk_update(batch, ['frameBudget', 'budgetChange'])

        new_location_finances, update_location_finances = self.update_forced_to_frame_locations()

        # Bulk create new LocationFinancial entries
        LocationFinancial.objects.bulk_create(new_location_finances, bulk_size)

        # Bulk update existing LocationFinancial entries
        if update_location_finances:
            for batch in batch_process(update_location_finances, bulk_size):
                LocationFinancial.objects.bulk_update(batch, ['frameBudget', 'budgetChange'])

        forced_to_frame_data_updated, _ = AppStateValueService.update_or_create(name="forcedToFrameDataUpdated", value=True)

        forced_to_frame_data_updated_serializer = AppStateValueSerializer(forced_to_frame_data_updated)

        return Response(
            data=forced_to_frame_data_updated_serializer.data,
            status=200
        )

    def update_forced_to_frame_projects(self):
        # updating the forced to frame schedule
        Project.objects.all().update(
            frameEstPlanningStart=F('estPlanningStart'),
            frameEstPlanningEnd=F('estPlanningEnd'),
            frameEstConstructionStart=F('estConstructionStart'),
            frameEstConstructionEnd=F('estConstructionEnd'),
            frameEstWarrantyPhaseStart=F('estWarrantyPhaseStart'),
            frameEstWarrantyPhaseEnd=F('estWarrantyPhaseEnd')
        )

        #updating the forced to frame finance data for projects
        planning_view_finances = ProjectFinancial.objects.filter(forFrameView=False)
        existing_frame_view_map = defaultdict(dict)
        frame_view_finances = ProjectFinancial.objects.filter(forFrameView=True)

        for finance in frame_view_finances:
            existing_frame_view_map[(finance.project_id, finance.year)] = finance

        new_finances = []
        update_finances = []

        for finance in planning_view_finances:
            key = (finance.project_id, finance.year)
            if key in existing_frame_view_map:
                # Update existing frame-view entry
                frame_view_finance = existing_frame_view_map[key]
                frame_view_finance.value = finance.value
                update_finances.append(frame_view_finance)
            else:
                # Create new frame-view entry
                new_finance = ProjectFinancial(
                    project_id=finance.project_id,
                    year=finance.year,
                    value=finance.value,
                    forFrameView=True
                )
                new_finances.append(new_finance)
        return new_finances, update_finances

    def update_forced_to_frame_classes(self):
        # updating forced to frame finance data for classes
        coordination_view_finances = ClassFinancial.objects.filter(forFrameView=False)
        existing_frame_view_map = defaultdict(dict)
        frame_view_finances = ClassFinancial.objects.filter(forFrameView=True)

        for finance in frame_view_finances:
            existing_frame_view_map[(finance.classRelation_id, finance.year)] = finance

        new_finances = []
        update_finances = []

        for finance in coordination_view_finances:
            key = (finance.classRelation_id, finance.year)
            if key in existing_frame_view_map:
                # Update existing frame-view entry
                frame_view_finance = existing_frame_view_map[key]
                frame_view_finance.frameBudget = finance.frameBudget
                frame_view_finance.budgetChange = finance.budgetChange
                update_finances.append(frame_view_finance)
            else:
                # Create new frame-view entry
                new_finance = ClassFinancial(
                    classRelation_id=finance.classRelation_id,
                    year=finance.year,
                    frameBudget=finance.frameBudget,
                    budgetChange=finance.budgetChange,
                    forFrameView=True
                )
                new_finances.append(new_finance)
        return new_finances, update_finances

    def update_forced_to_frame_locations(self):
        # updating forced to frame finance data for classes
        coordination_view_finances = LocationFinancial.objects.filter(forFrameView=False)
        existing_frame_view_map = defaultdict(dict)
        frame_view_finances = LocationFinancial.objects.filter(forFrameView=True)

        for finance in frame_view_finances:
            existing_frame_view_map[(finance.locationRelation_id, finance.year)] = finance

        new_finances = []
        update_finances = []

        for finance in coordination_view_finances:
            key = (finance.locationRelation_id, finance.year)
            if key in existing_frame_view_map:
                # Update existing frame-view entry
                frame_view_finance = existing_frame_view_map[key]
                frame_view_finance.frameBudget = finance.frameBudget
                frame_view_finance.budgetChange = finance.budgetChange
                update_finances.append(frame_view_finance)
            else:
                # Create new frame-view entry
                new_finance = LocationFinancial(
                    locationRelation_id=finance.locationRelation_id,
                    year=finance.year,
                    frameBudget=finance.frameBudget,
                    budgetChange=finance.budgetChange,
                    forFrameView=True
                )
                new_finances.append(new_finance)
        return new_finances, update_finances


    @transaction.atomic
    @action(
        methods=["patch"],
        detail=False,
        url_path=r"bulk-update",
        serializer_class=ProjectCreateSerializer,
        name="patch_bulk_projects",
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
                
                # IO-775: Capture original hkrId values BEFORE update for PW sync detection
                original_hkr_ids = {str(p.id): p.hkrId for p in qs}
                # Also capture which projects are getting hkrId in this request
                hkr_ids_in_request = {
                    projectData["id"]: projectData["data"].get("hkrId")
                    for projectData in data
                    if "hkrId" in projectData.get("data", {})
                }
                
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
                        forcedToFrame = finances.pop("forcedToFrame", False)

                        if year is None:
                            year = date.today().year
                        for field in finances.keys():
                            # skip the year field in finances
                            if field == "year":
                                continue
                            finance_year = ProjectFinancialService.convert_financial_field_to_year(field, year)
                            (
                                projectFinancialObject,
                                created,
                            ) = ProjectFinancialService.get_or_create(
                                year=finance_year,
                                project_id=Project(id=financeData["project"]).id,
                                for_frame_view=forcedToFrame,
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
                updated_projects = serializer.save()
                
                # IO-775: Trigger PW sync for projects where hkrId was added for the first time
                pw_sync_errors = []
                for updated_project in updated_projects:
                    project_id_str = str(updated_project.id)
                    original_hkr_id = original_hkr_ids.get(project_id_str)
                    new_hkr_id = hkr_ids_in_request.get(project_id_str)
                    
                    # Check if hkrId was added for the first time
                    hkr_id_added_first_time = (
                        new_hkr_id and
                        (not original_hkr_id or str(original_hkr_id).strip() == "")
                    )
                    
                    if hkr_id_added_first_time:
                        logger.info(f"BULK UPDATE: HKR ID added for first time to project '{updated_project.name}' (HKR ID: {updated_project.hkrId})")
                        try:
                            automatic_update_data = create_comprehensive_project_data(updated_project)
                            self.projectWiseService.sync_project_to_pw(
                                data=automatic_update_data, project=updated_project
                            )
                            logger.info(f"BULK UPDATE: PW sync completed for '{updated_project.name}'")
                        except Exception as e:
                            logger.error(f"BULK UPDATE: PW sync failed for '{updated_project.name}': {str(e)}")
                            pw_sync_errors.append({
                                "project": updated_project.name,
                                "hkrId": updated_project.hkrId,
                                "error": str(e)
                            })
                
                response_data = serializer.data
                if pw_sync_errors:
                    # Include PW sync errors in response but don't fail the request
                    response_data = {
                        "projects": serializer.data,
                        "pw_sync_errors": pw_sync_errors,
                        "message": f"Projects updated successfully but {len(pw_sync_errors)} PW sync(s) failed"
                    }
                
                return Response(data=response_data, status=200)
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

    def _sync_project_to_projectwise(self, request_data: dict, original_project: Project, updated_project: Project):
        """
        Handle ProjectWise synchronization with automatic update logic.

        Args:
            request_data: The data from the PATCH request
            original_project: Project state before update
            updated_project: Project state after update
        """
        # IO-775: Enhanced diagnostic logging for debugging sync issues
        hkr_id_in_request = 'hkrId' in request_data
        hkr_id_value = request_data.get('hkrId')
        original_had_hkr_id = bool(original_project.hkrId and str(original_project.hkrId).strip())
        
        logger.debug(
            f"PW SYNC CHECK for '{updated_project.name}': "
            f"hkrId_in_request={hkr_id_in_request}, "
            f"hkrId_value={hkr_id_value}, "
            f"original_hkrId={original_project.hkrId}, "
            f"original_had_hkr_id={original_had_hkr_id}"
        )
        
        # Check if hkrId is being added for the first time (automatic update)
        hkr_id_added_first_time = (
            hkr_id_in_request and
            hkr_id_value and
            not original_had_hkr_id
        )
        
        if not hkr_id_added_first_time:
            if hkr_id_in_request and hkr_id_value:
                logger.debug(f"PW SYNC SKIPPED for '{updated_project.name}': Project already had hkrId={original_project.hkrId}")
            elif hkr_id_in_request:
                logger.debug(f"PW SYNC SKIPPED for '{updated_project.name}': hkrId in request but value is falsy: {hkr_id_value}")
            else:
                logger.debug(f"PW SYNC SKIPPED for '{updated_project.name}': hkrId not in request data")

        if hkr_id_added_first_time:
            # This is the first time PW ID is added - perform automatic update with all project data
            logger.info(f"=" * 80)
            logger.info(f"HKR ID ADDED for first time to project '{updated_project.name}' (HKR ID: {updated_project.hkrId})")
            logger.info(f"Performing automatic comprehensive PW sync...")
            logger.info(f"=" * 80)

            try:
                # Create comprehensive data dict for automatic update
                automatic_update_data = create_comprehensive_project_data(updated_project)
                logger.debug(f"Automatic update data includes {len(automatic_update_data)} fields: {list(automatic_update_data.keys())}")

                self.projectWiseService.sync_project_to_pw(
                    data=automatic_update_data, project=updated_project
                )
                
                logger.info(f"Automatic PW sync completed successfully for project '{updated_project.name}'")
                
            except Exception as e:
                # Log detailed error but don't break the update
                logger.error(f"=" * 80)
                logger.error(f"AUTOMATIC PW SYNC FAILED for project '{updated_project.name}' (HKR ID: {updated_project.hkrId})")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error message: {str(e)}")
                logger.error(f"Project update succeeded but PW sync failed - data may be out of sync")
                logger.error(f"=" * 80)
                # Re-raise to make the failure visible in the UI
                raise ValidationError({
                    "hkrId": f"Project updated successfully but failed to sync to ProjectWise: {str(e)}. Please use 'Update to PW' button to retry."
                })

