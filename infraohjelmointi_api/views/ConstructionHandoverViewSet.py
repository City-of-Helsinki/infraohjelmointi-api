import logging
import uuid

from overrides import override
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination

from infraohjelmointi_api.models import ConstructionHandover
from infraohjelmointi_api.services.ConstructionHandoverHistoryService import (
    build_history,
)

from .BaseViewSet import BaseViewSet
from ..models import ProjectPhase, ProjectPhaseDetail
from ..permissions import IsConstructionManagementLead, IsPlanner, IsProjectManager
from ..services.ConstructionHandoverTransitionPermissionService import (
    ConstructionHandoverTransitionPermissionService,
)
from ..services.ProjectPhaseService import ProjectPhaseService
from ..services.ProjectPhaseDetailService import ProjectPhaseDetailService
from infraohjelmointi_api.serializers import (
    ConstructionHandoverGetSerializer,
    ConstructionHandoverCreateSerializer,
    ConstructionHandoverUpdateSerializer
)


logger = logging.getLogger(__name__)

class ConstructionHandoverViewSet(BaseViewSet):
    ALLOWED_STATUS_TRANSITIONS = {
        "DRAFT": ["SUBMITTED_TO_PROGRAMMER"],
        "SUBMITTED_TO_PROGRAMMER": ["SUBMITTED_TO_CONSTRUCTION"],
        "SUBMITTED_TO_CONSTRUCTION": ["PROJECT_MANAGER_NAMED", "DRAFT"],
        "PROJECT_MANAGER_NAMED": ["MOVED_TO_CONSTRUCTION_PREPARATION", "DRAFT"],
        "MOVED_TO_CONSTRUCTION_PREPARATION": ["DRAFT"],
    }
    
    """
    API endpoint that allows construction handovers to be viewed or edited.
    """

    @override
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ["list", "retrieve"]:
            return queryset.prefetch_related("financing", "financing__budgetItem")
        return queryset

    @override
    def get_serializer_class(self):
        """
        Overriden ModelViewSet class method to get appropriate serializer depending on the request action
        """
        if self.action in ["list", "retrieve"]:
            return ConstructionHandoverGetSerializer
        elif self.action == "create":
            return ConstructionHandoverCreateSerializer
        return ConstructionHandoverUpdateSerializer

    def _get_authenticated_user(self, request):
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            return user
        return None

    @override
    def perform_create(self, serializer):
        user = self._get_authenticated_user(self.request)
        if user:
            serializer.save(createdBy=user, updatedBy=user)
            return
        serializer.save()

    @override
    def create(self, request, *args, **kwargs):  
        project_id = request.data.get("project")
        # Check if there's an active handover for the project
        # (excluding MOVED_TO_CONSTRUCTION_PREPARATION status)
        # before allowing creation of a new one
        if project_id and ConstructionHandover.objects.filter(  
            project_id=project_id,  
        ).exclude(status="MOVED_TO_CONSTRUCTION_PREPARATION").exists():  
            return Response(  
                {"detail": "An active construction handover already exists for this project."},  
                status=status.HTTP_409_CONFLICT,  
            )  
        return super().create(request, *args, **kwargs)  

    @override
    def perform_update(self, serializer):
        user = self._get_authenticated_user(self.request)
        if user:
            serializer.save(updatedBy=user)
            return
        serializer.save()
    
    @override
    def partial_update(self, request, *args, **kwargs):
        """
        Overriden ModelViewSet class method to prevent updates if the handover is locked (not in DRAFT status)
        """
        instance = self.get_object()
        auto_transition_target_status = self._get_auto_transition_target_status(
            request=request,
            instance=instance,
        )
        should_auto_transition = auto_transition_target_status is not None

        if instance.is_locked and not should_auto_transition:
            return Response(
                {"detail": "Only construction handovers in DRAFT status can be edited."},
                status=status.HTTP_409_CONFLICT,
            )

        with transaction.atomic():
            response = super().partial_update(request, *args, **kwargs)
            if response.status_code != status.HTTP_200_OK or not should_auto_transition:
                return response

            instance.refresh_from_db()
            transition_error_response = self._transition_to_status(
                request=request,
                instance=instance,
                requested_status=auto_transition_target_status,
            )
            if transition_error_response:
                # Keep update+transition atomic: if transition fails, revert PATCH changes.
                transaction.set_rollback(True)
                return transition_error_response

            serializer = self.get_serializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
    
    @override
    def destroy(self, request, *args, **kwargs):
        """
        Overriden ModelViewSet class method to prevent deletion if the handover is not in DRAFT status
        """
        instance = self.get_object()
        if instance.is_locked:
            return Response(
                {"detail": "Only construction handovers in DRAFT status can be deleted."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    def _get_possible_status_transitions(self, current_status):
        return self.ALLOWED_STATUS_TRANSITIONS.get(current_status, [])

    def _is_project_manager(self, request):
        return IsProjectManager().user_in_project_manager_group(request=request)
    
    def _is_programmer(self, request):
        return IsPlanner().user_in_planner_group(request=request)
    
    def _is_construction_management_lead(self, request):
        return IsConstructionManagementLead().user_in_construction_management_lead_group(request=request)

    def _get_incoming_patch_fields(self, request):
        return set(getattr(request.data, "keys", lambda: [])())

    def _get_auto_transition_target_status(self, request, instance):
        if self._should_auto_transition_to_project_manager_named(request=request, instance=instance):
            return "PROJECT_MANAGER_NAMED"

        if self._should_auto_transition_to_moved_to_construction_preparation(
            request=request,
            instance=instance,
        ):
            return "MOVED_TO_CONSTRUCTION_PREPARATION"

        return None
    
    def _should_auto_transition_to_project_manager_named(self, request, instance):
        if instance.status != "SUBMITTED_TO_CONSTRUCTION":
            return False

        incoming_fields = self._get_incoming_patch_fields(request)
        return bool(incoming_fields & {"constructionProjectManager"})

    def _should_auto_transition_to_moved_to_construction_preparation(self, request, instance):
        if instance.status != "PROJECT_MANAGER_NAMED":
            return False

        incoming_fields = self._get_incoming_patch_fields(request)
        return incoming_fields == {"constructionProcurementMethod"}

    def _get_project_phase_or_none(self, phase_value):
        try:
            return ProjectPhaseService.get_by_value(value=phase_value)
        except ProjectPhase.DoesNotExist:
            logger.warning(
                "Skipping project phase sync for missing ProjectPhase value '%s'.",
                phase_value,
            )
            return None

    def _get_project_phase_detail_or_none(self, phase_detail_value):
        return ProjectPhaseDetailService.find_by_value(value=phase_detail_value)

    def _sync_procurement_method(self, project, instance, project_update_fields):
        # Keep project's procurement method aligned with the handover value.
        if (
            project.constructionProcurementMethod_id
            != instance.constructionProcurementMethod_id
        ):
            project.constructionProcurementMethod = instance.constructionProcurementMethod
            project_update_fields.append("constructionProcurementMethod")

    def _sync_submitted_to_construction(
        self,
        project,
        instance,
        project_update_fields,
        handover_update_fields,
    ):
        # Move project to construction-wait state and store previous values for rollback to DRAFT.
        construction_wait_phase = self._get_project_phase_or_none("constructionWait")
        construction_wait_phase_detail = self._get_project_phase_detail_or_none("otherReason")

        if construction_wait_phase and project.phase_id != construction_wait_phase.id:
            instance.previousProjectPhase = project.phase
            handover_update_fields.append("previousProjectPhase")
            project.phase = construction_wait_phase
            project_update_fields.append("phase")

        if (
            construction_wait_phase_detail
            and project.phaseDetail_id != construction_wait_phase_detail.id
        ):
            instance.previousProjectPhaseDetail = project.phaseDetail
            handover_update_fields.append("previousProjectPhaseDetail")
            project.phaseDetail = construction_wait_phase_detail
            project_update_fields.append("phaseDetail")

    def _sync_project_manager_named(
        self,
        project,
        instance,
        project_update_fields,
    ):
        # Mirror selected construction project manager to the project.
        if project.personConstruction_id != instance.constructionProjectManager_id:
            project.personConstruction = instance.constructionProjectManager
            project_update_fields.append("personConstruction")

        self._sync_procurement_method(
            project=project,
            instance=instance,
            project_update_fields=project_update_fields,
        )

    def _sync_moved_to_construction_preparation(
        self,
        project,
        instance,
        project_update_fields,
    ):
        # Advance project to construction-preparation phase and contract-preparation detail.
        construction_preparation_phase = self._get_project_phase_or_none(
            "constructionPreparation"
        )
        construction_preparation_phase_detail = self._get_project_phase_detail_or_none(
            "contractPreparation"
        )

        if (
            construction_preparation_phase
            and project.phase_id != construction_preparation_phase.id
        ):
            project.phase = construction_preparation_phase
            project_update_fields.append("phase")

        if (
            construction_preparation_phase_detail
            and project.phaseDetail_id != construction_preparation_phase_detail.id
        ):
            project.phaseDetail = construction_preparation_phase_detail
            project_update_fields.append("phaseDetail")

        self._sync_procurement_method(
            project=project,
            instance=instance,
            project_update_fields=project_update_fields,
        )

    def _sync_draft(
        self,
        project,
        instance,
        project_update_fields,
        handover_update_fields,
    ):
        # Restore previously saved phase values when transition returns to DRAFT.
        # PersonConstruction and constructionProcurementMethod are not reverted to previous values.
        
        if not instance.previousProjectPhase_id:
            return

        project.phase = instance.previousProjectPhase
        project_update_fields.append("phase")

        # previousProjectPhaseDetail may intentionally be None.
        # Restore it whenever we have a saved previous phase.
        if project.phaseDetail_id != instance.previousProjectPhaseDetail_id:
            project.phaseDetail = instance.previousProjectPhaseDetail
            project_update_fields.append("phaseDetail")

        instance.previousProjectPhase = None
        handover_update_fields.append("previousProjectPhase")
        instance.previousProjectPhaseDetail = None
        handover_update_fields.append("previousProjectPhaseDetail")

    def _persist_synced_transition_fields(
        self,
        project,
        instance,
        project_update_fields,
        handover_update_fields,
    ):
        # Persist only changed fields to avoid unnecessary writes.
        if project_update_fields:
            project.save(update_fields=project_update_fields)

        if handover_update_fields:
            instance.save(update_fields=handover_update_fields)

    def _sync_project_fields_for_transition(self, instance, requested_status):
        project = instance.project
        project_update_fields = []
        handover_update_fields = []

        transition_sync_handlers = {
            "SUBMITTED_TO_CONSTRUCTION": lambda: self._sync_submitted_to_construction(
                project=project,
                instance=instance,
                project_update_fields=project_update_fields,
                handover_update_fields=handover_update_fields,
            ),
            "PROJECT_MANAGER_NAMED": lambda: self._sync_project_manager_named(
                project=project,
                instance=instance,
                project_update_fields=project_update_fields,
            ),
            "MOVED_TO_CONSTRUCTION_PREPARATION": lambda: self._sync_moved_to_construction_preparation(
                project=project,
                instance=instance,
                project_update_fields=project_update_fields,
            ),
            "DRAFT": lambda: self._sync_draft(
                project=project,
                instance=instance,
                project_update_fields=project_update_fields,
                handover_update_fields=handover_update_fields,
            ),
        }

        sync_handler = transition_sync_handlers.get(requested_status)
        if sync_handler:
            sync_handler()

        self._persist_synced_transition_fields(
            project=project,
            instance=instance,
            project_update_fields=project_update_fields,
            handover_update_fields=handover_update_fields,
        )

    def _transition_to_status(self, request, instance, requested_status):
        possible_statuses = self._get_possible_status_transitions(instance.status)

        valid_statuses = {choice[0] for choice in instance.STATUS_CHOICES}
        if requested_status not in valid_statuses:
            return Response(
                {
                    "detail": f"Invalid status '{requested_status}'.",
                    "currentStatus": instance.status,
                    "possibleTransitions": possible_statuses,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if requested_status not in possible_statuses:
            return Response(
                {
                    "detail": "Invalid status transition.",
                    "currentStatus": instance.status,
                    "possibleTransitions": possible_statuses,
                },
                status=status.HTTP_409_CONFLICT,
            )

        if (
            requested_status == "PROJECT_MANAGER_NAMED"
            and instance.constructionProjectManager_id in (None, "")
        ):
            return Response(
                {
                    "detail": "constructionProjectManager is required for this transition.",
                    "currentStatus": instance.status,
                    "possibleTransitions": possible_statuses,
                },
                status=status.HTTP_409_CONFLICT,
            )

        if (
            requested_status == "MOVED_TO_CONSTRUCTION_PREPARATION"
            and instance.constructionProcurementMethod_id in (None, "")
        ):
            return Response(
                {
                    "detail": "constructionProcurementMethod is required for this transition.",
                    "currentStatus": instance.status,
                    "possibleTransitions": possible_statuses,
                },
                status=status.HTTP_409_CONFLICT,
            )
        
        if not ConstructionHandoverTransitionPermissionService.is_transition_allowed(
            requested_status=requested_status,
            user=self._get_authenticated_user(request),
            project=instance.project,
            is_project_manager=self._is_project_manager(request),
            is_programmer=self._is_programmer(request),
            is_construction_management_lead=self._is_construction_management_lead(request),
        ):
            return Response(
                {
                    "detail": "You do not have permission to perform this transition.",
                    "currentStatus": instance.status,
                    "possibleTransitions": possible_statuses,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        user = self._get_authenticated_user(request)
        with transaction.atomic():
            instance.status = requested_status
            if user:
                instance.updatedBy = user
            instance.save()
            self._sync_project_fields_for_transition(
                instance=instance,
                requested_status=requested_status,
            )

        return None
    
    @action(methods=["post"], detail=True, url_path=r"transitions")
    def transitions(self, request, pk=None):
        instance = self.get_object()
        possible_statuses = self._get_possible_status_transitions(instance.status)
        requested_status = request.data.get("to")

        if requested_status is None:
            return Response(
                {
                    "detail": "Field 'to' is required.",
                    "currentStatus": instance.status,
                    "possibleTransitions": possible_statuses,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transition_error_response = self._transition_to_status(
            request=request,
            instance=instance,
            requested_status=requested_status,
        )
        if transition_error_response:
            return transition_error_response

        return Response(
            {
                "currentStatus": instance.status,
                "possibleTransitions": self._get_possible_status_transitions(instance.status),
            },
            status=status.HTTP_200_OK,
        )

    @action(
        methods=["get"],
        detail=True,
        url_path=r"history",
        name="get_construction_handover_history",
    )
    def get_construction_handover_history(self, request, pk=None):
        """
        Change history for a single handover, reconstructed from its
        django-simple-history records and returned newest-first as
        who-changed-what-when events (same shape as the project history feed).
        """
        try:
            uuid.UUID(str(pk))
        except (ValueError, TypeError):
            return Response(
                {"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )

        handover = self.get_object()

        events = build_history(handover)

        paginator = PageNumberPagination()
        paginator.page_size = 100
        paginator.page_size_query_param = "pageSize"
        page = paginator.paginate_queryset(events, request, view=self)
        return paginator.get_paginated_response(page)
