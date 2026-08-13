import uuid

from overrides import override
from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser

from infraohjelmointi_api.models import ConstructionHandover, ConstructionHandoverAttachment

from .BaseViewSet import BaseViewSet
from ..permissions import IsConstructionManagementLead, IsPlanner, IsProjectManager
from ..services.ConstructionHandoverTransitionPermissionService import (
    ConstructionHandoverTransitionPermissionService,
)
from ..utils.upload_validation import validate_handover_attachment
from infraohjelmointi_api.serializers import (
    ConstructionHandoverGetSerializer,
    ConstructionHandoverCreateSerializer,
    ConstructionHandoverUpdateSerializer,
    ConstructionHandoverAttachmentSerializer,
)

# Mirrors LOCKED_HANDOVER_EDIT_ERROR in ConstructionHandoverFinancingViewSet: the
# ticket asks for attachments to follow the same DRAFT-only rule as financing rows.
LOCKED_HANDOVER_ATTACHMENT_ERROR = (
    "Attachments can only be added or removed while the construction handover is in DRAFT status."
)


class ConstructionHandoverViewSet(BaseViewSet):
    ALLOWED_STATUS_TRANSITIONS = {
        "DRAFT": ["SUBMITTED_TO_PROGRAMMER"],
        "SUBMITTED_TO_PROGRAMMER": ["SUBMITTED_TO_CONSTRUCTION"],
        "SUBMITTED_TO_CONSTRUCTION": ["PROJECT_MANAGER_NAMED"],
        "PROJECT_MANAGER_NAMED": ["MOVED_TO_CONSTRUCTION_PREPARATION"],
        "MOVED_TO_CONSTRUCTION_PREPARATION": [],
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

    @action(
        methods=["get", "post"],
        detail=True,
        url_path=r"attachments",
        url_name="attachments",
        name="handover_attachments",
        parser_classes=[MultiPartParser, FormParser],
    )
    def attachments(self, request, pk):
        """List or upload attachments for a handover (IO-857).

        GET  /construction-handovers/<id>/attachments/  -> ConstructionHandoverAttachment[]
        POST /construction-handovers/<id>/attachments/  -> created rows (multipart, field 'file' x N)
        """
        handover = self.get_object()
        if request.method == "GET":
            return Response(
                ConstructionHandoverAttachmentSerializer(
                    handover.attachments.all(), many=True, context={"request": request}
                ).data
            )

        # Same rule as financing rows: content may only change while in DRAFT.
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
        with transaction.atomic():
            created = [
                ConstructionHandoverAttachment.objects.create(
                    handover=handover,
                    file=f,
                    originalName=f.name,
                    contentType=(f.content_type or "").lower(),
                    size=f.size or 0,
                    uploadedBy=uploader,
                )
                for f in files
            ]
        return Response(
            ConstructionHandoverAttachmentSerializer(
                created, many=True, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        methods=["get"],
        detail=True,
        url_path=r"attachments/(?P<attachmentId>[^/.]+)/download",
        url_name="download-attachment",
        name="download_handover_attachment",
    )
    def download_attachment(self, request, pk, attachmentId):
        """Stream one attachment back to the caller (IO-857).

        GET /construction-handovers/<id>/attachments/<aid>/download/

        Proxied through the API rather than handing out a storage URL, so the blob
        container stays private and normal viewset permissions apply. At the 500 KB
        cap this is cheap; if PDF support raises the cap to ~25 MB it is worth
        switching to short-lived SAS URLs so a download does not occupy a worker.
        """
        attachment = self._get_attachment_or_404(pk, attachmentId)
        if not attachment.file:
            raise NotFound("Attachment has no stored file.")

        response = FileResponse(
            attachment.file.open("rb"),
            as_attachment=True,
            filename=attachment.originalName,
            content_type=attachment.contentType or "application/octet-stream",
        )
        return response

    @action(
        methods=["delete"],
        detail=True,
        url_path=r"attachments/(?P<attachmentId>[^/.]+)",
        url_name="delete-attachment",
        name="delete_handover_attachment",
    )
    def delete_attachment(self, request, pk, attachmentId):
        """Delete one attachment (IO-857).

        DELETE /construction-handovers/<id>/attachments/<aid>/  -> 204
        """
        handover = self.get_object()
        if handover.is_locked:
            return Response(
                {"detail": LOCKED_HANDOVER_ATTACHMENT_ERROR},
                status=status.HTTP_409_CONFLICT,
            )
        attachment = self._get_attachment_or_404(pk, attachmentId, handover=handover)
        # Remove the blob before the row, so a failed storage delete does not leave
        # orphaned bytes referenced by a row that is already gone.
        attachment.file.delete(save=False)
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_attachment_or_404(self, pk, attachmentId, handover=None):
        """Resolve an attachment scoped to its handover, validating the UUID first.

        Scoping by handover matters: without it, a caller who can read one handover
        could pass another handover's attachment id and get its file.
        """
        try:
            uuid.UUID(str(attachmentId))
        except ValueError:
            raise ValidationError({"attachmentId": "Invalid UUID."})
        if handover is None:
            handover = self.get_object()
        return get_object_or_404(
            ConstructionHandoverAttachment, pk=attachmentId, handover=handover
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