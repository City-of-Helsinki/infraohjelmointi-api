from overrides import override
from rest_framework import status
from rest_framework.response import Response

from infraohjelmointi_api.models import ConstructionHandoverFinancing
from infraohjelmointi_api.serializers import ConstructionHandoverFinancingSerializer

from .BaseViewSet import BaseViewSet


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
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.handover.is_locked:
            return Response(
                {"detail": "Only construction handovers in DRAFT status can be edited."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)
