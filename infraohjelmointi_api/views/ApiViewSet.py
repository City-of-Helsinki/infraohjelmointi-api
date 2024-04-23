from datetime import datetime

from .BaseViewSet import BaseViewSet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from infraohjelmointi_api.serializers import (
    ProjectClassSerializer,
    ProjectGetSerializer,
    ProjectGroupSerializer,
    ProjectLocationSerializer
)
from infraohjelmointi_api.services import (
    ProjectClassService,
    ProjectGroupService,
    ProjectLocationService,
    ProjectService
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
import logging

logger = logging.getLogger("infraohjelmointi_api")

from drf_yasg.utils import swagger_auto_schema

class ApiViewSet(BaseViewSet):
    """
    API endpoint that allows API connections
    """

    http_method_names = ['get']

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    serializer_class = ProjectGetSerializer


    @swagger_auto_schema(
            operation_description = """
            `GET /api/projects/`

            Get all projects.
            """,
            )
    @method_decorator(cache_page(60 * 60 * 6))
    @action(
        methods=["get"],
        detail=False,
        url_path=r"projects",
        serializer_class=ProjectGetSerializer,
        name="get_api_all_projects",
    )
    def get_api_all_projects(self, request):
        start = datetime.now()
        projects = ProjectService.get_all_projects()
        projectsSerialized = ProjectGetSerializer(projects, many=True).data

        end = datetime.now()
        time_diff = end - start

        logger.debug("### Request took " + str(time_diff))

        return Response(projectsSerialized)


    @swagger_auto_schema(
            operation_description = """
            `GET /api/groups/`

            Get all project groups.
            """,
            )
    @action(
        methods=["get"],
        detail=False,
        url_path=r"groups",
        serializer_class=ProjectGroupSerializer,
        name="get_api_all_groups",
    )
    def get_api_all_groups(self, request):
        groups = ProjectGroupService.get_all_groups()
        serialized = ProjectGroupSerializer(groups, many=True).data

        return Response(serialized)


    @swagger_auto_schema(
            operation_description = """
            `GET /api/classes/`

            Get all hierarchy classes. Includes both Coordinator and Programmer classes.
            """,
            )
    @action(
        methods=["get"],
        detail=False,
        url_path=r"classes",
        serializer_class=ProjectClassSerializer,
        name="get_api_all_classes",
    )
    def get_api_all_classes(self, request):
        classes = ProjectClassService.list_all_classes()
        serialized = ProjectClassSerializer(classes, many=True).data

        return Response(serialized)


    @swagger_auto_schema(
            operation_description = """
            `GET /api/locations/`

            Get all project locations.
            """,
            )
    @action(
        methods=["get"],
        detail=False,
        url_path=r"locations",
        serializer_class=ProjectLocationSerializer,
        name="get_api_all_locations",
    )
    def get_api_all_locations(self, request):
        locations = ProjectLocationService().list_all_locations()
        serialized = ProjectLocationSerializer(locations, many=True).data

        return Response(serialized)
