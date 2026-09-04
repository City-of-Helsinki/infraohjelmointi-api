from overrides import override
from django.db.models import CharField, Value
from helusers.oidc import ApiTokenAuthentication
from rest_framework import mixins, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from infraohjelmointi_api.models import ConstructionHandover, Project
from infraohjelmointi_api.serializers.ProjectTaskSerializer import (
    ProjectTaskSerializer,
    TASK_TYPE_NAME_CONSTRUCTION_PROJECT_MANAGER,
)
from infraohjelmointi_api.permissions import IsConstructionManagementLead

HANDOVER_STATUS_SUBMITTED_TO_CONSTRUCTION = "SUBMITTED_TO_CONSTRUCTION"


class ProjectTasksViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Get the list of project tasks for the current user based on their role.
    """

    serializer_class = ProjectTaskSerializer
    http_method_names = ["get"]
    permission_classes = [IsAuthenticated]
    authentication_classes = [ApiTokenAuthentication, SessionAuthentication]

    def _is_construction_management_lead(self, request):
        return IsConstructionManagementLead().user_in_construction_management_lead_group(
            request=request
        )

    @override
    def get_queryset(self):
        if self._is_construction_management_lead(self.request): 
            # Get all projects that have a construction handover submitted to construction
            handover_project_ids = ConstructionHandover.objects.filter(
                status=HANDOVER_STATUS_SUBMITTED_TO_CONSTRUCTION
            ).values_list("project_id", flat=True)

            return (
                Project.objects.filter(id__in=handover_project_ids)
                .annotate(
                    taskType=Value(
                        TASK_TYPE_NAME_CONSTRUCTION_PROJECT_MANAGER, output_field=CharField()
                    )
                ).select_related("constructionProcurementMethod")
            )
        
        return Project.objects.none()

    @override
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)