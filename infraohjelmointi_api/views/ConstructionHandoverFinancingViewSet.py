import uuid

from overrides import override
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from infraohjelmointi_api.models import ConstructionHandoverFinancing, Project
from infraohjelmointi_api.serializers import ConstructionHandoverFinancingSerializer

from .BaseViewSet import BaseViewSet


LOCKED_HANDOVER_EDIT_ERROR = "Only construction handovers in DRAFT status can be edited."


class ConstructionHandoverFinancingViewSet(BaseViewSet):
    """API endpoint that allows construction handover financing rows to be viewed or edited."""

    queryset = ConstructionHandoverFinancing.objects.select_related("handover", "budgetItem")
    serializer_class = ConstructionHandoverFinancingSerializer

    @override
    def get_queryset(self):
        queryset = super().get_queryset()
        handover_id = self.request.query_params.get("handover")
        project_id = self.request.query_params.get("project")

        if handover_id:
            queryset = queryset.filter(handover_id=handover_id)
        elif project_id:
            queryset = queryset.filter(handover__project_id=project_id).exclude(
                handover__status="MOVED_TO_CONSTRUCTION_PREPARATION"
            )

        return queryset

    @override
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        handover = serializer.validated_data.get("handover")
        if handover and handover.is_locked:
            return Response(
                {"detail": LOCKED_HANDOVER_EDIT_ERROR},
                status=status.HTTP_409_CONFLICT,
            )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @override
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if instance.handover.is_locked:
            return Response(
                {"detail": LOCKED_HANDOVER_EDIT_ERROR},
                status=status.HTTP_409_CONFLICT,
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        
        return Response(serializer.data)

    @override
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.handover.is_locked:
            return Response(
                {"detail": LOCKED_HANDOVER_EDIT_ERROR},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="lookup-project-number")
    def lookup_project_number(self, request):
        """
        GET /construction-handover-financings/lookup-project-number/?budgetItem={uuid}

        Returns the SAP project number for a budget item by matching Project.siteId.
        Returns null when no matching project is found.
        """
        budget_item_id = request.query_params.get("budgetItem")
        if not budget_item_id:
            return Response(
                {"budgetItem": "This query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            budget_item_uuid = uuid.UUID(budget_item_id)
        except ValueError:
            return Response(
                {"budgetItem": "Invalid UUID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        project = Project.objects.filter(siteId_id=budget_item_uuid).first()
        project_number = project.sapProject if project else None
        return Response({"projectNumber": project_number})
