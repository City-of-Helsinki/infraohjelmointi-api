import json
from collections import defaultdict
from datetime import date
from ..BaseViewSet import BaseViewSet
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from infraohjelmointi_api.models import (
    Project, ProjectFinancial
)
from infraohjelmointi_api.serializers import (
    ProjectGetSerializer, ProjectFinancialSerializer
)
import uuid
from django.http import StreamingHttpResponse
from .utils import generate_response, generate_response_not_found, generate_streaming_response, send_logger_api_generate_data_start

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

import logging

logger = logging.getLogger("infraohjelmointi_api")

class_parameter = openapi.Parameter(
    "class",
    in_=openapi.IN_QUERY,
    description="Get all projects by class ID",
    type=openapi.TYPE_STRING,
)


class ApiProjectsViewSet(BaseViewSet):
    http_method_names = ["get"]

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = (
        Project.objects.all()
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
        )
        .prefetch_related("favPersons", "hashTags", "finances")
    )

    serializer_class = ProjectGetSerializer

    @swagger_auto_schema(
        operation_description="""
        `GET /api/projects/{id}`

        Get specific project data.
        """,
    )
    def retrieve(self, request, pk=None):
        return generate_response(self, request.user.id, pk, request.path)


    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "class",
                openapi.IN_QUERY,
                description="The ID of the project class (UUID)",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=False,
            ),
        ],
        operation_description="""
        `GET /api/projects/`

        Get all projects.

        `GET /api/projects/?class={id}`
        
        Get all projects filtered by the specified project class ID.
        """,
    )
    def list(self, request, *args, **kwargs):
        path = request.path
        if self.request.query_params.get("class"):
            path += "?class=" + self.request.query_params.get("class")

        send_logger_api_generate_data_start(request.user.id, path)
        project_class_id = self.request.query_params.get("class")
        queryset = self.queryset
        if project_class_id is not None:
            try:
                queryset = queryset.filter(projectClass__id=uuid.UUID(project_class_id))
            except Exception:
                return StreamingHttpResponse(json.dumps({"error":"Invalid UUID"}),status=400, content_type = "application/json")
        else:
            queryset = Project.objects.all()
        self.queryset = queryset

        year = date.today().year
        finances = ProjectFinancialSerializer(
            ProjectFinancial.objects.filter(
                year__in=range(year, year + 11),
                forFrameView=False,
            ),
            many=True,
            context={"discard_FK": False}
        ).data

        projects_to_finances = defaultdict(list)
        for f in finances:
            projects_to_finances[f["project"]].append(f)

        serializer_context = {
            "projects_to_finances": projects_to_finances
        }

        return StreamingHttpResponse(
            generate_streaming_response(
                self.queryset,
                self.serializer_class,
                request.user.id,
                path,
                chunk_size=500,
                serializer_context=serializer_context
            ),
            content_type="application/json",
        )
