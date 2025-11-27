from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.TalpaProjectOpeningSerializer import TalpaProjectOpeningSerializer
from infraohjelmointi_api.models import TalpaProjectOpening
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from overrides import override
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import uuid
import logging

logger = logging.getLogger("infraohjelmointi_api")

# Custom actions that should be accessible with just IsAuthenticated
TALPA_READ_ONLY_ACTIONS = ["get_by_project", "get_priorities", "get_subjects"]
TALPA_WRITE_ACTIONS = ["send_to_talpa"]


class TalpaProjectOpeningViewSet(BaseViewSet):
    """
    API endpoint that allows Talpa project opening data to be viewed or edited.
    """

    serializer_class = TalpaProjectOpeningSerializer

    @override
    def get_permissions(self):
        """
        Override permissions for custom Talpa actions.
        
        The BaseViewSet permission classes check for specific action names,
        but custom actions like 'get_by_project' are not in those lists.
        This override allows authenticated users to access Talpa-specific actions.
        """
        # If permission_classes is empty (e.g., in tests), allow all
        if not self.permission_classes:
            return []
        if self.action in TALPA_READ_ONLY_ACTIONS + TALPA_WRITE_ACTIONS:
            return [IsAuthenticated()]
        return super().get_permissions()

    @override
    def get_queryset(self):
        """Get queryset with related objects"""
        return TalpaProjectOpening.objects.select_related(
            "project",
            "projectType",
            "serviceClass",
            "assetClass",
            "projectNumberRange",
            "createdBy",
            "updatedBy",
        ).all()

    @override
    def update(self, request, *args, **kwargs):
        """Override update to check if form is locked"""
        instance = self.get_object()
        if instance.is_locked:
            return Response(
                {"detail": "Form is locked. Cannot update when status is 'sent_to_talpa'."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    @override
    def partial_update(self, request, *args, **kwargs):
        """Override partial_update to check if form is locked"""
        instance = self.get_object()
        if instance.is_locked:
            return Response(
                {"detail": "Form is locked. Cannot update when status is 'sent_to_talpa'."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)

    @override
    def destroy(self, request, *args, **kwargs):
        """Override destroy to prevent deleting locked forms"""
        instance = self.get_object()
        if instance.is_locked:
            return Response(
                {"detail": "Form is locked. Cannot delete when status is 'sent_to_talpa'."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get TalpaProjectOpening by project ID",
        manual_parameters=[
            openapi.Parameter(
                "project_id",
                openapi.IN_PATH,
                description="Project UUID",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
            ),
        ],
        responses={200: TalpaProjectOpeningSerializer, 404: "Not found"},
    )
    @action(
        methods=["get"],
        detail=False,
        url_path=r"by-project/(?P<project_id>[0-9a-f-]+)",
        name="get_by_project",
    )
    def get_by_project(self, request, project_id=None):
        """
        Custom action to get TalpaProjectOpening by project_id

        URL Parameters
        ----------
        project_id : UUID string

        Usage
        ----------
        talpa-project-opening/by-project/<project_id>/

        Returns
        -------
        JSON
            TalpaProjectOpening instance or 404 if not found
        """
        try:
            uuid.UUID(str(project_id))  # Validate UUID
            try:
                # Use get_queryset() to benefit from select_related optimization
                instance = self.get_queryset().get(project_id=project_id)
                serializer = self.get_serializer(instance)
                return Response(serializer.data)
            except TalpaProjectOpening.DoesNotExist:
                return Response(
                    {"detail": "TalpaProjectOpening not found for this project."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        except ValueError:
            return Response(
                {"detail": "Invalid UUID format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Required fields that must be filled before sending to Talpa
    REQUIRED_FIELDS_FOR_TALPA = [
        ("projectName", "Project name (SAP nimi)"),
        ("subject", "Subject (Aihe)"),
        ("projectType", "Project type (Laji)"),
        ("projectNumberRange", "Project number range (Projektinumeroväli)"),
    ]

    def _validate_form_completeness(self, instance):
        """
        Validate that all required fields are filled before sending to Talpa.
        Returns list of missing field names, or empty list if complete.
        """
        missing = []
        for field_name, display_name in self.REQUIRED_FIELDS_FOR_TALPA:
            value = getattr(instance, field_name, None)
            if value is None or value == "":
                missing.append(display_name)
        return missing

    @swagger_auto_schema(
        operation_description="Send Talpa opening to Talpa and lock the form. Updates status to 'sent_to_talpa'. Validates required fields before locking.",
        responses={200: TalpaProjectOpeningSerializer, 400: "Already sent or missing required fields"},
    )
    @action(
        methods=["post"],
        detail=True,
        url_path=r"send-to-talpa",
        name="send_to_talpa",
    )
    def send_to_talpa(self, request, pk=None):
        """
        Custom action to update status to "sent_to_talpa" and lock the form.
        
        Validates that all required fields are filled before locking.
        Once locked, the form cannot be edited or deleted.

        Usage
        ----------
        POST talpa-project-opening/<id>/send-to-talpa/

        Returns
        -------
        JSON
            Updated TalpaProjectOpening instance
            
        Errors
        ------
        400: Form already sent, or missing required fields
        """
        instance = self.get_object()

        # Check if already sent
        if instance.status == "sent_to_talpa":
            return Response(
                {"detail": "Form has already been sent to Talpa."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate form completeness before locking
        missing_fields = self._validate_form_completeness(instance)
        if missing_fields:
            return Response(
                {
                    "detail": "Cannot send to Talpa. The following required fields are missing:",
                    "missing_fields": missing_fields,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update status
        instance.status = "sent_to_talpa"
        if hasattr(request.user, "person"):
            instance.updatedBy = request.user.person
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
        url_path=r"priorities",
        name="get_priorities",
    )
    def get_priorities(self, request):
        """
        Get available priority choices

        Usage
        ----------
        GET talpa-project-opening/priorities/

        Returns
        -------
        JSON
            List of priority choices
        """
        priorities = [
            {"value": choice[0], "label": choice[1]}
            for choice in TalpaProjectOpening.PRIORITY_CHOICES
        ]
        return Response(priorities)

    @action(
        methods=["get"],
        detail=False,
        url_path=r"subjects",
        name="get_subjects",
    )
    def get_subjects(self, request):
        """
        Get available subject choices

        Usage
        ----------
        GET talpa-project-opening/subjects/

        Returns
        -------
        JSON
            List of subject choices
        """
        subjects = [
            {"value": choice[0], "label": choice[1]}
            for choice in TalpaProjectOpening.SUBJECT_CHOICES
        ]
        return Response(subjects)

