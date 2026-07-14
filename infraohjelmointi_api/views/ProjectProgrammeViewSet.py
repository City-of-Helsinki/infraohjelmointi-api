import uuid

from overrides import override
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from infraohjelmointi_api.models import ProjectProgramme
from infraohjelmointi_api.serializers import (
    ProjectProgrammeGetSerializer,
    ProjectProgrammeTransitionToCompletedSerializer,
    ProjectProgrammeUpdateSerializer,
)

from .BaseViewSet import BaseViewSet


class ProjectProgrammeViewSet(BaseViewSet):
    """API endpoint that allows project programmes to be viewed or edited."""

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    @override
    def get_queryset(self):
        queryset = ProjectProgramme.objects.all()
        if self.action in ["list", "retrieve", "get_by_project"]:
            return queryset.select_related(
                "project",
                "basicInfo",
                "designCriteria",
                "trafficPlanningCriteria",
                "urbanSpacingPlanningCriteria",
                "maintenanceNeeds",
                "interactionAndRelatedProjects",
                "otherAttachments",
            )
        return queryset

    @override
    def get_serializer_class(self):
        if self.action in ["list", "retrieve", "get_by_project"]:
            return ProjectProgrammeGetSerializer
        if self.action == "transitions":
            return ProjectProgrammeTransitionToCompletedSerializer
        return ProjectProgrammeUpdateSerializer

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
    def perform_update(self, serializer):
        user = self._get_authenticated_user(self.request)
        if user:
            serializer.save(updatedBy=user)
            return
        serializer.save()

    @action(methods=["get"], detail=False, url_path=r"by-project/(?P<project_id>[0-9a-f-]+)")
    def get_by_project(self, request, project_id=None):
        try:
            uuid.UUID(str(project_id))
        except ValueError:
            return Response({"detail": "Invalid UUID format."}, status=status.HTTP_400_BAD_REQUEST)

        instance = self.get_queryset().filter(project_id=project_id).first()
        if not instance:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(self.get_serializer(instance).data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True, url_path=r"switch-type")
    def switch_type(self, request, pk=None):
        instance = self.get_object()
        serializer = ProjectProgrammeUpdateSerializer(
            instance,
            data={"briefProjectProgramme": not instance.briefProjectProgramme},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        get_serializer = ProjectProgrammeGetSerializer(
            instance,
            context=self.get_serializer_context(),
        )
        return Response(get_serializer.data, status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True, url_path=r"transitions")
    def transitions(self, request, pk=None):
        instance = self.get_object()
        serializer = ProjectProgrammeTransitionToCompletedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_status = serializer.validated_data["to"]
        if instance.status == requested_status:
            return Response(
                {"detail": "Project programme is already in the requested status."},
                status=status.HTTP_409_CONFLICT,
            )

        instance.status = requested_status
        user = self._get_authenticated_user(request)
        if user:
            instance.updatedBy = user
        instance.save()

        return Response(
            {
                "currentStatus": instance.status,
            },
            status=status.HTTP_200_OK,
        )
