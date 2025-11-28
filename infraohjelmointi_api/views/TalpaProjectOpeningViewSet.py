import uuid
import logging

from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from overrides import override
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.models import TalpaProjectOpening
from infraohjelmointi_api.serializers import TalpaProjectOpeningSerializer
from infraohjelmointi_api.services import TalpaExcelService

logger = logging.getLogger("infraohjelmointi_api")

TALPA_ACTIONS = ["get_by_project", "get_priorities", "get_subjects", "download_excel", "send_to_talpa"]


class TalpaProjectOpeningViewSet(BaseViewSet):
    """API endpoint for Talpa project opening data."""

    serializer_class = TalpaProjectOpeningSerializer

    REQUIRED_FIELDS = [
        ("projectName", "SAP nimi"),
        ("subject", "Aihe"),
        ("projectType", "Laji"),
        ("projectNumberRange", "Projektinumeroväli"),
    ]

    @override
    def get_permissions(self):
        if not self.permission_classes:
            return []
        if self.action in TALPA_ACTIONS:
            return [IsAuthenticated()]
        return super().get_permissions()

    @override
    def get_queryset(self):
        return TalpaProjectOpening.objects.select_related(
            "project", "projectType", "serviceClass", 
            "assetClass", "projectNumberRange", "createdBy", "updatedBy"
        ).all()

    def _check_locked(self, instance):
        if instance.is_locked:
            return Response(
                {"detail": "Form is locked. Cannot modify when status is 'sent_to_talpa'."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def _set_updated_by(self, request, instance):
        if hasattr(request.user, "person"):
            instance.updatedBy = request.user.person

    @override
    def update(self, request, *args, **kwargs):
        error = self._check_locked(self.get_object())
        return error if error else super().update(request, *args, **kwargs)

    @override
    def partial_update(self, request, *args, **kwargs):
        error = self._check_locked(self.get_object())
        return error if error else super().partial_update(request, *args, **kwargs)

    @override
    def destroy(self, request, *args, **kwargs):
        error = self._check_locked(self.get_object())
        return error if error else super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get TalpaProjectOpening by project ID",
        manual_parameters=[
            openapi.Parameter("project_id", openapi.IN_PATH, type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
        ],
        responses={200: TalpaProjectOpeningSerializer, 404: "Not found"},
    )
    @action(methods=["get"], detail=False, url_path=r"by-project/(?P<project_id>[0-9a-f-]+)")
    def get_by_project(self, request, project_id=None):
        try:
            uuid.UUID(str(project_id))
            instance = self.get_queryset().get(project_id=project_id)
            return Response(self.get_serializer(instance).data)
        except ValueError:
            return Response({"detail": "Invalid UUID format."}, status=status.HTTP_400_BAD_REQUEST)
        except TalpaProjectOpening.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Lock form and update status to 'sent_to_talpa'",
        responses={200: TalpaProjectOpeningSerializer, 400: "Validation error"},
    )
    @action(methods=["post"], detail=True, url_path=r"send-to-talpa")
    def send_to_talpa(self, request, pk=None):
        instance = self.get_object()

        if instance.status == "sent_to_talpa":
            return Response({"detail": "Already sent to Talpa."}, status=status.HTTP_400_BAD_REQUEST)

        missing = [name for field, name in self.REQUIRED_FIELDS if not getattr(instance, field, None)]
        if missing:
            return Response(
                {"detail": "Missing required fields.", "missing_fields": missing},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance.status = "sent_to_talpa"
        self._set_updated_by(request, instance)
        instance.save()
        return Response(self.get_serializer(instance).data)

    @action(methods=["get"], detail=False, url_path=r"priorities")
    def get_priorities(self, request):
        return Response([{"value": v, "label": l} for v, l in TalpaProjectOpening.PRIORITY_CHOICES])

    @action(methods=["get"], detail=False, url_path=r"subjects")
    def get_subjects(self, request):
        return Response([{"value": v, "label": l} for v, l in TalpaProjectOpening.SUBJECT_CHOICES])

    @swagger_auto_schema(
        operation_description="Download Excel for Talpa submission",
        responses={200: openapi.Response(description="Excel file", schema=openapi.Schema(type=openapi.TYPE_FILE))},
    )
    @action(methods=["get"], detail=True, url_path=r"download-excel")
    def download_excel(self, request, pk=None):
        instance = self.get_object()
        service = TalpaExcelService()

        if instance.status not in ["sent_to_talpa", "project_number_opened"]:
            instance.status = "excel_generated"
            self._set_updated_by(request, instance)
            instance.save()

        response = HttpResponse(
            service.generate_excel(instance).getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{service.get_filename(instance)}"'
        return response
