import logging
import uuid

from overrides import override
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser

from infraohjelmointi_api.models import ConstructionHandover, ConstructionHandoverAttachment
from infraohjelmointi_api.services.ConstructionHandoverHistoryService import (
    build_history,
)

from .BaseViewSet import BaseViewSet
from ..models import ProjectPhase
from ..permissions import (
    IsAdmin,
    IsConstructionManagementLead,
    IsCoordinator,
    IsPlanner,
    IsProjectManager,
)
from ..services.ConstructionHandoverTransitionPermissionService import (
    ConstructionHandoverTransitionPermissionService,
)
from ..services.ProjectPhaseService import ProjectPhaseService
from ..services.ProjectPhaseDetailService import ProjectPhaseDetailService
from ..utils.stored_files import (
    cleanup_files_on_error,
    display_file_name,
    stored_file_response,
)
from ..utils.upload_validation import validate_handover_attachment
from infraohjelmointi_api.serializers import (
    ConstructionHandoverGetSerializer,
    ConstructionHandoverCreateSerializer,
    ConstructionHandoverUpdateSerializer,
    ConstructionHandoverAttachmentSerializer,
)


logger = logging.getLogger(__name__)
# Mirrors LOCKED_HANDOVER_EDIT_ERROR in ConstructionHandoverFinancingViewSet: the
# ticket asks attachments to follow the same rule as financing rows, which is
# ConstructionHandover.is_locked (editable in DRAFT and SUBMITTED_TO_PROGRAMMER).
LOCKED_HANDOVER_ATTACHMENT_ERROR = (
    "Attachments can only be added or removed while the construction handover is in "
    "DRAFT or SUBMITTED_TO_PROGRAMMER status."
)


class ConstructionHandoverViewSet(BaseViewSet):
    # Flow: DRAFT -> SUBMITTED_TO_PROGRAMMER -> SUBMITTED_TO_CONSTRUCTION -> PROJECT_MANAGER_NAMED
    # -> MOVED_TO_CONSTRUCTION_PREPARATION. Each status can step back one, or return to DRAFT.
    # Project sync on entry:
    #   SUBMITTED_TO_CONSTRUCTION (from SUBMITTED_TO_PROGRAMMER): saves phase/phaseDetail on the
    #     handover, sets constructionWait/otherReason.
    #   PROJECT_MANAGER_NAMED: personConstruction, constructionProcurementMethod, staraProcurementReason;
    #     from MOVED_TO_CONSTRUCTION_PREPARATION also reverts the phase to constructionWait/otherReason.
    #   MOVED_TO_CONSTRUCTION_PREPARATION: constructionPreparation/contractPreparation + procurement fields.
    #   SUBMITTED_TO_PROGRAMMER / DRAFT: restore the saved phase/phaseDetail.
    # Phase changes are skipped if the project phase was changed manually; person and procurement are never reverted.
    ALLOWED_STATUS_TRANSITIONS = {
        "DRAFT": ["SUBMITTED_TO_PROGRAMMER"],
        "SUBMITTED_TO_PROGRAMMER": ["SUBMITTED_TO_CONSTRUCTION", "DRAFT"],
        "SUBMITTED_TO_CONSTRUCTION": ["PROJECT_MANAGER_NAMED", "SUBMITTED_TO_PROGRAMMER", "DRAFT"],
        "PROJECT_MANAGER_NAMED": ["MOVED_TO_CONSTRUCTION_PREPARATION", "SUBMITTED_TO_CONSTRUCTION", "DRAFT"],
        "MOVED_TO_CONSTRUCTION_PREPARATION": ["PROJECT_MANAGER_NAMED", "DRAFT"],
    }

    # Project phase the handover sets when it enters each status.
    HANDOVER_SET_PROJECT_PHASES = {
        "SUBMITTED_TO_CONSTRUCTION": "constructionWait",
        "PROJECT_MANAGER_NAMED": "constructionWait",
        "MOVED_TO_CONSTRUCTION_PREPARATION": "constructionPreparation",
    }
    
    """
    API endpoint that allows construction handovers to be viewed or edited.
    """

    @override
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ["list", "retrieve"]:
            # attachments is prefetched too, else embedding it in the GET serializer
            # is an N+1 across a handover list.
            return queryset.prefetch_related(
                "financing", "financing__budgetItem", "attachments"
            )
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
        Overriden ModelViewSet class method to prevent updates if the handover is locked (not in DRAFT or SUBMITTED_TO_PROGRAMMER status)
        """
        instance = self.get_object()
        auto_transition_target_status = self._get_auto_transition_target_status(
            request=request,
            instance=instance,
        )
        should_auto_transition = auto_transition_target_status is not None

        if instance.is_locked and not should_auto_transition:
            return Response(
                {"detail": "Only construction handovers in DRAFT or SUBMITTED_TO_PROGRAMMER status can be edited."},
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
        Overriden ModelViewSet class method to prevent deletion if the handover is not in DRAFT or SUBMITTED_TO_PROGRAMMER status
        """
        instance = self.get_object()
        if instance.is_locked:
            return Response(
                {"detail": "Only construction handovers in DRAFT or SUBMITTED_TO_PROGRAMMER status can be deleted."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @action(
        methods=["get"],
        detail=True,
        url_path=r"attachments",
        url_name="attachments",
        name="handover_attachments",
        parser_classes=[MultiPartParser, FormParser],
    )
    def attachments(self, request, pk):
        """List the attachments of a handover (IO-857).

        GET /construction-handovers/<id>/attachments/  -> ConstructionHandoverAttachment[]
        """
        handover = self.get_object()
        return Response(
            ConstructionHandoverAttachmentSerializer(
                handover.attachments.all(), many=True, context={"request": request}
            ).data
        )

    # A separate action name for POST on the same URL keeps the permission
    # allowlists honest: granting "attachments" (read) never grants uploads,
    # even in role classes that do not check the HTTP method.
    @attachments.mapping.post
    def upload_attachment(self, request, pk):
        """Upload attachments to a handover (IO-857).

        POST /construction-handovers/<id>/attachments/  -> created rows (multipart, field 'file' x N)
        """
        handover = self.get_object()
        # Same rule as financing rows: ConstructionHandover.is_locked.
        if handover.is_locked:
            return Response(
                {"detail": LOCKED_HANDOVER_ATTACHMENT_ERROR},
                status=status.HTTP_409_CONFLICT,
            )

        files = request.FILES.getlist("file")
        if not files:
            raise ValidationError({"file": "At least one file is required."})

        # Validate the whole batch first so one bad file rejects the request before
        # any row or blob is written, rather than leaving a half-applied upload.
        for f in files:
            validate_handover_attachment(f)

        uploader = self._get_authenticated_user(request)
        created = []
        with cleanup_files_on_error(created), transaction.atomic():
            for f in files:
                attachment = ConstructionHandoverAttachment(
                    handover=handover,
                    file=f,
                    originalName=display_file_name(f.name),
                    contentType=(f.content_type or "").lower(),
                    size=f.size or 0,
                    uploadedBy=uploader,
                )
                # Track before saving: the file is written ahead of the INSERT.
                created.append(attachment)
                attachment.save()
        return Response(
            ConstructionHandoverAttachmentSerializer(
                created, many=True, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        methods=["get"],
        detail=True,
        url_path=r"attachments/(?P<attachment_id>[^/.]+)/download",
        url_name="download-attachment",
        name="download_handover_attachment",
    )
    def download_attachment(self, request, pk, attachment_id):
        """Stream one attachment back to the caller (IO-857).

        GET /construction-handovers/<id>/attachments/<aid>/download/

        Always proxied through the API, never a storage URL: see
        utils/stored_files.py for why (the container SAS token must stay
        server-side, and short-lived per-blob SAS links are not possible with
        SAS-only auth).
        """
        attachment = self._get_attachment_or_404(pk, attachment_id)
        if not attachment.file:
            raise NotFound("Attachment has no stored file.")

        return stored_file_response(
            attachment.file,
            attachment.contentType,
            attachment.originalName,
            as_attachment=True,
        )

    @action(
        methods=["delete"],
        detail=True,
        url_path=r"attachments/(?P<attachment_id>[^/.]+)",
        url_name="delete-attachment",
        name="delete_handover_attachment",
    )
    def delete_attachment(self, request, pk, attachment_id):
        """Delete one attachment (IO-857).

        DELETE /construction-handovers/<id>/attachments/<aid>/  -> 204
        """
        handover = self.get_object()
        if handover.is_locked:
            return Response(
                {"detail": LOCKED_HANDOVER_ATTACHMENT_ERROR},
                status=status.HTTP_409_CONFLICT,
            )
        attachment = self._get_attachment_or_404(pk, attachment_id, handover=handover)
        # The file is removed on commit by the post_delete signal in signals.py.
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_attachment_or_404(self, pk, attachment_id, handover=None):
        """Resolve an attachment scoped to its handover, validating the UUID first.

        Scoping by handover matters: without it, a caller who can read one handover
        could pass another handover's attachment id and get its file.
        """
        try:
            uuid.UUID(str(attachment_id))
        except ValueError:
            raise ValidationError({"attachmentId": "Invalid UUID."})
        if handover is None:
            handover = self.get_object()
        return get_object_or_404(
            ConstructionHandoverAttachment, pk=attachment_id, handover=handover
        )

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
        allowed_fields = {"constructionProcurementMethod", "staraProcurementReason"}
        return (
            "constructionProcurementMethod" in incoming_fields
            and incoming_fields.issubset(allowed_fields)
        )

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

    @staticmethod
    def _set_if_changed(obj, field, value, update_fields):
        if getattr(obj, f"{field}_id") != getattr(value, "pk", None):
            setattr(obj, field, value)
            update_fields.append(field)

    @staticmethod
    def _project_in_phase(project, phase_value):
        return project.phase is not None and project.phase.value == phase_value

    def _set_project_phase(self, project, phase_value, phase_detail_value, project_update_fields):
        # Missing lookup rows are skipped rather than clearing the project's values.
        phase = self._get_project_phase_or_none(phase_value)
        if phase is None:
            return
        self._set_if_changed(project, "phase", phase, project_update_fields)
        phase_detail = self._get_project_phase_detail_or_none(phase_detail_value)
        if phase_detail is not None:
            self._set_if_changed(project, "phaseDetail", phase_detail, project_update_fields)

    def _sync_procurement(self, project, instance, project_update_fields):
        self._set_if_changed(
            project, "constructionProcurementMethod", instance.constructionProcurementMethod, project_update_fields
        )
        self._set_if_changed(
            project, "staraProcurementReason", instance.staraProcurementReason, project_update_fields
        )

    def _restore_previous_project_phase(
        self, project, instance, previous_status, project_update_fields, handover_update_fields
    ):
        handover_set_phase_value = self.HANDOVER_SET_PROJECT_PHASES.get(previous_status)
        if handover_set_phase_value is None:
            return

        # A manually changed phase is kept; saved values may intentionally be None.
        if self._project_in_phase(project, handover_set_phase_value):
            self._set_if_changed(project, "phase", instance.previousProjectPhase, project_update_fields)
            self._set_if_changed(
                project, "phaseDetail", instance.previousProjectPhaseDetail, project_update_fields
            )

        instance.previousProjectPhase = None
        instance.previousProjectPhaseDetail = None
        handover_update_fields.extend(["previousProjectPhase", "previousProjectPhaseDetail"])

    def _sync_project_fields_for_transition(self, instance, requested_status, previous_status):
        project = instance.project
        project_update_fields = []
        handover_update_fields = []

        if requested_status in ("DRAFT", "SUBMITTED_TO_PROGRAMMER"):
            self._restore_previous_project_phase(
                project, instance, previous_status, project_update_fields, handover_update_fields
            )

        elif requested_status == "SUBMITTED_TO_CONSTRUCTION":
            # Stepping back from PROJECT_MANAGER_NAMED keeps the values saved on first entry.
            if previous_status == "SUBMITTED_TO_PROGRAMMER":
                instance.previousProjectPhase = project.phase
                instance.previousProjectPhaseDetail = project.phaseDetail
                handover_update_fields.extend(["previousProjectPhase", "previousProjectPhaseDetail"])
                self._set_project_phase(project, "constructionWait", "otherReason", project_update_fields)

        elif requested_status == "PROJECT_MANAGER_NAMED":
            if (
                previous_status == "MOVED_TO_CONSTRUCTION_PREPARATION"
                and self._project_in_phase(project, "constructionPreparation")
            ):
                self._set_project_phase(project, "constructionWait", "otherReason", project_update_fields)
            self._set_if_changed(
                project, "personConstruction", instance.constructionProjectManager, project_update_fields
            )
            self._sync_procurement(project, instance, project_update_fields)

        elif requested_status == "MOVED_TO_CONSTRUCTION_PREPARATION":
            self._set_project_phase(
                project, "constructionPreparation", "contractPreparation", project_update_fields
            )
            self._sync_procurement(project, instance, project_update_fields)

        if project_update_fields:
            project.save(update_fields=project_update_fields)
        if handover_update_fields:
            instance.save(update_fields=handover_update_fields)

    def _transition_error_response(self, instance, detail, http_status):
        return Response(
            {
                "detail": detail,
                "currentStatus": instance.status,
                "possibleTransitions": self._get_possible_status_transitions(instance.status),
            },
            status=http_status,
        )

    def _get_transition_error(self, request, instance, requested_status):
        """Return (detail, http_status) if the transition is not allowed, else None."""
        if requested_status not in {choice[0] for choice in instance.STATUS_CHOICES}:
            return f"Invalid status '{requested_status}'.", status.HTTP_400_BAD_REQUEST

        if requested_status not in self._get_possible_status_transitions(instance.status):
            return "Invalid status transition.", status.HTTP_409_CONFLICT

        if requested_status == "PROJECT_MANAGER_NAMED" and not instance.constructionProjectManager_id:
            return "constructionProjectManager is required for this transition.", status.HTTP_409_CONFLICT

        if (
            requested_status == "MOVED_TO_CONSTRUCTION_PREPARATION"
            and not instance.constructionProcurementMethod_id
        ):
            return "constructionProcurementMethod is required for this transition.", status.HTTP_409_CONFLICT

        # Once moved to preparation a new handover may exist; don't reopen this one next to it.
        if (
            instance.status == "MOVED_TO_CONSTRUCTION_PREPARATION"
            and ConstructionHandover.objects.filter(project_id=instance.project_id)
            .exclude(pk=instance.pk)
            .exclude(status="MOVED_TO_CONSTRUCTION_PREPARATION")
            .exists()
        ):
            return "An active construction handover already exists for this project.", status.HTTP_409_CONFLICT

        if not ConstructionHandoverTransitionPermissionService.is_transition_allowed(
            requested_status=requested_status,
            current_status=instance.status,
            user=self._get_authenticated_user(request),
            project=instance.project,
            is_project_manager=self._is_project_manager(request),
            is_programmer=self._is_programmer(request),
            is_construction_management_lead=self._is_construction_management_lead(request),
        ):
            return "You do not have permission to perform this transition.", status.HTTP_403_FORBIDDEN

        return None

    def _transition_to_status(self, request, instance, requested_status):
        error = self._get_transition_error(request, instance, requested_status)
        if error:
            return self._transition_error_response(instance, *error)

        user = self._get_authenticated_user(request)
        previous_status = instance.status
        with transaction.atomic():
            instance.status = requested_status
            if user:
                instance.updatedBy = user
            instance.save()
            self._sync_project_fields_for_transition(
                instance=instance,
                requested_status=requested_status,
                previous_status=previous_status,
            )

        return None
    
    @action(
        methods=["post"],
        detail=True,
        url_path=r"transitions",
        permission_classes=[
            IsCoordinator
            | IsPlanner 
            | IsProjectManager 
            | IsConstructionManagementLead
            | IsAdmin
        ],
    )
    def transitions(self, request, pk=None):
        instance = self.get_object()
        requested_status = request.data.get("to")

        if requested_status is None:
            return self._transition_error_response(
                instance, "Field 'to' is required.", status.HTTP_400_BAD_REQUEST
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
        paginator.max_page_size = 500
        page = paginator.paginate_queryset(events, request, view=self)
        return paginator.get_paginated_response(page)
