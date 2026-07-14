import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from overrides import override
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from infraohjelmointi_api.models import (
    ProjectProgramme,
    ProjectProgrammeBasicInfo,
    ProjectProgrammeDesignCriteria,
    ProjectProgrammeInteractionAndRelatedProjects,
    ProjectProgrammeMaintenanceNeeds,
    ProjectProgrammeOtherAttachments,
    ProjectProgrammeTrafficPlanningCriteria,
    ProjectProgrammeUrbanSpacingPlanningCriteria,
)
from infraohjelmointi_api.serializers import (
    ProjectProgrammeGetSerializer,
    ProjectProgrammeTransitionToCompletedSerializer,
    ProjectProgrammeUpdateSerializer,
)

from .BaseViewSet import BaseViewSet


class ProjectProgrammeViewSet(BaseViewSet):
    """API endpoint that allows project programmes to be viewed or edited."""

    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    SECTION_CONFIG = {
        "basicInfo": {
            "model": ProjectProgrammeBasicInfo,
            "required_fields": [
                "projectName",
                "district",
                "projectProgrammeCompiler",
                "personsInvolved",
                "summary",
                "strategyGoals",
                "projectSize",
                "risks",
                "studyAndPlanningNeeds",
                "planningAndImplementationFeasibility",
            ],
        },
        "designCriteria": {
            "model": ProjectProgrammeDesignCriteria,
            "required_fields": [
                "guidingZoningRegulations",
                "siteValuesProtectionAndSignificance",
                "relationshipToPublicAreaServices",
            ],
        },
        "trafficPlanningCriteria": {
            "model": ProjectProgrammeTrafficPlanningCriteria,
            "required_fields": [
                "pedestrianTraffic",
                "bicycleTraffic",
                "serviceAndPickupTraffic",
                "otherTraffic",
                "accessibility",
                "noiseManagement",
                "winterMaintenance",
            ],
        },
        "urbanSpacingPlanningCriteria": {
            "model": ProjectProgrammeUrbanSpacingPlanningCriteria,
            "required_fields": [
                "targetUrbanAppearance",
                "surfaceMaterials",
                "structures",
                "technicalNetworksAndSystems",
                "lighting",
                "greenery",
                "lumoConsiderationAndProtection",
                "natureTypes",
                "equipmentAndFurnishings",
                "waters",
                "stormwaterManagement",
            ],
        },
        "maintenanceNeeds": {
            "model": ProjectProgrammeMaintenanceNeeds,
            "required_fields": ["maintenanceNeeds"],
        },
        "interactionAndRelatedProjects": {
            "model": ProjectProgrammeInteractionAndRelatedProjects,
            "required_fields": [
                "maintenanceNeeds",
                "collaborationAndExperts",
                "interactionNotes",
            ],
        },
        "otherAttachments": {
            "model": ProjectProgrammeOtherAttachments,
            "required_fields": [],
        },
    }
    BRIEF_SECTION_KEYS = ["basicInfo"]

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
        if self.action in ["transitions", "section_transitions"]:
            return ProjectProgrammeTransitionToCompletedSerializer
        return ProjectProgrammeUpdateSerializer

    def _get_relevant_section_keys(self, project_programme):
        if project_programme.briefProjectProgramme:
            return self.BRIEF_SECTION_KEYS
        return list(self.SECTION_CONFIG.keys())

    def _get_section_config(self, section_key, project_programme=None):
        if section_key not in self.SECTION_CONFIG:
            return None

        if project_programme is None:
            return self.SECTION_CONFIG[section_key]

        if section_key not in self._get_relevant_section_keys(project_programme):
            return None

        return self.SECTION_CONFIG[section_key]

    def _get_section_instance(self, project_programme, section_key):
        try:
            return getattr(project_programme, section_key)
        except ObjectDoesNotExist:
            return None

    def _get_missing_required_fields(self, instance, required_fields):
        missing_fields = []
        for field_name in required_fields:
            value = getattr(instance, field_name, None)
            if value is None:
                missing_fields.append(field_name)
                continue

            if isinstance(value, str) and not value.strip():
                missing_fields.append(field_name)

        return missing_fields

    def _create_section_instance(self, project_programme, section_key, requested_status, user=None):
        config = self.SECTION_CONFIG[section_key]
        defaults = {"project_programme": project_programme, "status": requested_status}

        if section_key == "basicInfo":
            defaults["projectName"] = project_programme.project.name or ""
            defaults["district"] = (
                project_programme.project.projectDistrict.name
                if project_programme.project.projectDistrict
                else ""
            )

        if user:
            defaults["createdBy"] = user
            defaults["updatedBy"] = user

        return config["model"].objects.create(**defaults)

    def _get_section_completion_errors(self, project_programme, section_key):
        config = self._get_section_config(section_key, project_programme)
        if config is None:
            return None

        section_instance = self._get_section_instance(project_programme, section_key)
        if section_instance is None:
            return list(config["required_fields"])

        return self._get_missing_required_fields(
            section_instance,
            config["required_fields"],
        )

    def _get_project_programme_completion_errors(self, project_programme):
        missing_fields = {}
        for section_key in self._get_relevant_section_keys(project_programme):
            section_missing_fields = self._get_section_completion_errors(
                project_programme,
                section_key,
            )
            if section_missing_fields:
                missing_fields[section_key] = section_missing_fields

        return missing_fields

    def _build_missing_fields_response(self, detail, missing_fields):
        return Response(
            {
                "detail": detail,
                "missing_fields": missing_fields,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _save_section_status(self, section_instance, requested_status, user=None):
        section_instance.status = requested_status
        if user:
            section_instance.updatedBy = user
        section_instance.save()

    def _complete_project_programme_sections(self, project_programme, user=None):
        for section_key in self._get_relevant_section_keys(project_programme):
            section_instance = self._get_section_instance(project_programme, section_key)
            if section_instance is None:
                section_instance = self._create_section_instance(
                    project_programme,
                    section_key,
                    "COMPLETE",
                    user=user,
                )
            elif section_instance.status == "DRAFT":
                self._save_section_status(section_instance, "COMPLETE", user=user)

        project_programme.status = "COMPLETE"
        if user:
            project_programme.updatedBy = user
        project_programme.save()

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

        user = self._get_authenticated_user(request)

        if requested_status == "COMPLETE":
            missing_fields = self._get_project_programme_completion_errors(instance)
            if missing_fields:
                return self._build_missing_fields_response(
                    "Project programme cannot be transitioned to COMPLETE.",
                    missing_fields,
                )

            with transaction.atomic():
                self._complete_project_programme_sections(instance, user=user)
        else:
            instance.status = requested_status
            if user:
                instance.updatedBy = user
            instance.save()

        return Response(
            {
                "currentStatus": instance.status,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        methods=["post"],
        detail=True,
        url_path=r"sections/(?P<section_key>[^/.]+)/transitions",
    )
    def section_transitions(self, request, pk=None, section_key=None):
        instance = self.get_object()
        section_config = self._get_section_config(section_key, instance)
        if section_config is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectProgrammeTransitionToCompletedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_status = serializer.validated_data["to"]
        section_instance = self._get_section_instance(instance, section_key)
        current_status = section_instance.status if section_instance else "DRAFT"

        if current_status == requested_status:
            return Response(
                {"detail": "Project programme section is already in the requested status."},
                status=status.HTTP_409_CONFLICT,
            )

        user = self._get_authenticated_user(request)

        if requested_status == "COMPLETE":
            missing_fields = self._get_section_completion_errors(instance, section_key)
            if missing_fields:
                return self._build_missing_fields_response(
                    "Project programme section cannot be transitioned to COMPLETE.",
                    {section_key: missing_fields},
                )

            if section_instance is None:
                section_instance = self._create_section_instance(
                    instance,
                    section_key,
                    "COMPLETE",
                    user=user,
                )
            else:
                self._save_section_status(section_instance, "COMPLETE", user=user)
        else:
            if section_instance is None:
                section_instance = self._create_section_instance(
                    instance,
                    section_key,
                    "DRAFT",
                    user=user,
                )
            else:
                self._save_section_status(section_instance, "DRAFT", user=user)

        return Response(
            {
                "currentStatus": section_instance.status,
            },
            status=status.HTTP_200_OK,
        )
