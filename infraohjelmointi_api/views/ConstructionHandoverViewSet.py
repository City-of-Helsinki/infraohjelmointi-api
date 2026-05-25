from overrides import override
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action

from infraohjelmointi_api.models import ConstructionHandover

from .BaseViewSet import BaseViewSet
from ..permissions import IsConstructionManagementLead, IsPlanner, IsProjectManager
from ..services.ConstructionHandoverTransitionPermissionService import (
    ConstructionHandoverTransitionPermissionService,
)
from infraohjelmointi_api.serializers import (
    ConstructionHandoverGetSerializer,
    ConstructionHandoverCreateSerializer,
    ConstructionHandoverUpdateSerializer
)

class ConstructionHandoverViewSet(BaseViewSet):
    ALLOWED_STATUS_TRANSITIONS = {
        "DRAFT": ["SUBMITTED_TO_PROGRAMMER"],
        "SUBMITTED_TO_PROGRAMMER": ["SUBMITTED_TO_CONSTRUCTION"],
        "SUBMITTED_TO_CONSTRUCTION": ["PROJECT_MANAGER_NAMED"],
        "PROJECT_MANAGER_NAMED": ["MOVED_TO_CONSTRUCTION_PREPARATION"],
        "MOVED_TO_CONSTRUCTION_PREPARATION": [],
    }

    AUTO_TRANSITION_TRIGGER_FIELDS = {
        "constructionProjectManager",
        "constructionProcurementMethod",
    }
    
    """
    API endpoint that allows construction handovers to be viewed or edited.
    """

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
        return bool(incoming_fields & self.AUTO_TRANSITION_TRIGGER_FIELDS)

    def _should_auto_transition_to_moved_to_construction_preparation(self, request, instance):
        if instance.status != "PROJECT_MANAGER_NAMED":
            return False

        incoming_fields = self._get_incoming_patch_fields(request)
        return incoming_fields == {"constructionProcurementMethod"}

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
        instance.status = requested_status
        if user:
            instance.updatedBy = user
        instance.save()

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