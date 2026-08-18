import uuid

from overrides import override
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from infraohjelmointi_api.models import (
    ProjectProgrammeBasicInfo,
    ProjectProgrammeDesignCriteria,
    ProjectProgrammeInteractionAndRelatedProjects,
    ProjectProgramme,
    ProjectProgrammeLink,
    ProjectProgrammeMaintenanceNeeds,
    ProjectProgrammeOtherAttachments,
    ProjectProgrammeTrafficPlanningCriteria,
    ProjectProgrammeUrbanSpacingPlanningCriteria,
)
from infraohjelmointi_api.serializers import (
    ProjectProgrammeBasicInfoGetSerializer,
    ProjectProgrammeBasicInfoUpdateSerializer,
    ProjectProgrammeCreateSerializer,
    ProjectProgrammeDesignCriteriaGetSerializer,
    ProjectProgrammeDesignCriteriaUpdateSerializer,
    ProjectProgrammeGetSerializer,
    ProjectProgrammeInteractionAndRelatedProjectsGetSerializer,
    ProjectProgrammeInteractionAndRelatedProjectsUpdateSerializer,
    ProjectProgrammeLinkGetSerializer,
    ProjectProgrammeLinkUpdateSerializer,
    ProjectProgrammeMaintenanceNeedsGetSerializer,
    ProjectProgrammeMaintenanceNeedsUpdateSerializer,
    ProjectProgrammeOtherAttachmentsGetSerializer,
    ProjectProgrammeOtherAttachmentsUpdateSerializer,
    ProjectProgrammeStatusTransitionSerializer,
    ProjectProgrammeTrafficPlanningCriteriaGetSerializer,
    ProjectProgrammeTrafficPlanningCriteriaUpdateSerializer,
    ProjectProgrammeUpdateSerializer,
    ProjectProgrammeUrbanSpacingPlanningCriteriaGetSerializer,
    ProjectProgrammeUrbanSpacingPlanningCriteriaUpdateSerializer,
)

from .BaseViewSet import BaseViewSet


class ProjectProgrammeViewSet(BaseViewSet):
    """API endpoint that allows project programmes to be viewed or edited."""

    NOT_FOUND_DETAIL = "Not found."
    
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    LINK_SECTION_MODELS = (
        ProjectProgrammeBasicInfo,
        ProjectProgrammeDesignCriteria,
        ProjectProgrammeTrafficPlanningCriteria,
        ProjectProgrammeUrbanSpacingPlanningCriteria,
        ProjectProgrammeMaintenanceNeeds,
        ProjectProgrammeInteractionAndRelatedProjects,
        ProjectProgrammeOtherAttachments,
    )

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
        if self.action == "create":
            return ProjectProgrammeCreateSerializer
        if self.action == "transitions":
            return ProjectProgrammeStatusTransitionSerializer
        return ProjectProgrammeUpdateSerializer

    def _get_authenticated_user(self, request):
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            return user
        return None

    def _get_section_instance_for_link(self, content_type, object_id):
        model_class = content_type.model_class()
        if model_class not in self.LINK_SECTION_MODELS:
            return None

        return model_class.objects.filter(pk=object_id).first()

    @staticmethod
    def _section_belongs_to_programme(section_instance, programme):
        if section_instance is None:
            return False
        return getattr(section_instance, "project_programme_id", None) == programme.id

    def _handle_section(self, request, related_name, update_serializer_class, get_serializer_class):
        programme = self.get_object()
        if programme.is_locked:
            return Response(
                {"detail": "Only sections of project programmes in DRAFT status can be edited."},
                status=status.HTTP_409_CONFLICT,
            )

        existing_section = getattr(programme, related_name, None)

        if request.method == "POST":
            if existing_section is not None:
                return Response(
                    {"detail": "Section already exists. Use PATCH to update it."},
                    status=status.HTTP_409_CONFLICT,
                )
            data = {**request.data, "project_programme": str(programme.id)}
            serializer = update_serializer_class(data=data)
            serializer.is_valid(raise_exception=True)
            user = self._get_authenticated_user(request)
            save_kwargs = {"createdBy": user, "updatedBy": user} if user else {}
            serializer.save(**save_kwargs)
            return Response(
                get_serializer_class(serializer.instance).data,
                status=status.HTTP_201_CREATED,
            )

        # PATCH
        if existing_section is None:
            return Response(
                {"detail": "Section does not exist. Use POST to create it."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if "project_programme" in request.data:
            return Response(
                {"project_programme": "Section parent project programme cannot be changed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = update_serializer_class(
            existing_section,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        user = self._get_authenticated_user(request)
        save_kwargs = {"updatedBy": user} if user else {}
        serializer.save(**save_kwargs)
        return Response(
            get_serializer_class(serializer.instance).data,
            status=status.HTTP_200_OK,
        )

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

    @override
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_locked:
            return Response(
                {"detail": "Only project programmes in DRAFT status can be deleted."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @action(methods=["get"], detail=False, url_path=r"by-project/(?P<project_id>[^/.]+)")
    def get_by_project(self, request, project_id=None):
        try:
            uuid.UUID(str(project_id))
        except ValueError:
            return Response({"detail": "Invalid UUID format."}, status=status.HTTP_400_BAD_REQUEST)

        instance = self.get_queryset().filter(project_id=project_id).first()
        if not instance:
            return Response({"detail": self.NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)

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
        serializer = ProjectProgrammeStatusTransitionSerializer(data=request.data)
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

    @action(methods=["post", "patch"], detail=True, url_path="sections/basic-info")
    def section_basic_info(self, request, pk=None):
        return self._handle_section(
            request,
            related_name="basicInfo",
            update_serializer_class=ProjectProgrammeBasicInfoUpdateSerializer,
            get_serializer_class=ProjectProgrammeBasicInfoGetSerializer,
        )

    @action(methods=["post", "patch"], detail=True, url_path="sections/design-criteria")
    def section_design_criteria(self, request, pk=None):
        return self._handle_section(
            request,
            related_name="designCriteria",
            update_serializer_class=ProjectProgrammeDesignCriteriaUpdateSerializer,
            get_serializer_class=ProjectProgrammeDesignCriteriaGetSerializer,
        )

    @action(methods=["post", "patch"], detail=True, url_path="sections/traffic-planning-criteria")
    def section_traffic_planning_criteria(self, request, pk=None):
        return self._handle_section(
            request,
            related_name="trafficPlanningCriteria",
            update_serializer_class=ProjectProgrammeTrafficPlanningCriteriaUpdateSerializer,
            get_serializer_class=ProjectProgrammeTrafficPlanningCriteriaGetSerializer,
        )

    @action(
        methods=["post", "patch"],
        detail=True,
        url_path="sections/urban-spacing-planning-criteria",
    )
    def section_urban_spacing_planning_criteria(self, request, pk=None):
        return self._handle_section(
            request,
            related_name="urbanSpacingPlanningCriteria",
            update_serializer_class=ProjectProgrammeUrbanSpacingPlanningCriteriaUpdateSerializer,
            get_serializer_class=ProjectProgrammeUrbanSpacingPlanningCriteriaGetSerializer,
        )

    @action(methods=["post", "patch"], detail=True, url_path="sections/maintenance-needs")
    def section_maintenance_needs(self, request, pk=None):
        return self._handle_section(
            request,
            related_name="maintenanceNeeds",
            update_serializer_class=ProjectProgrammeMaintenanceNeedsUpdateSerializer,
            get_serializer_class=ProjectProgrammeMaintenanceNeedsGetSerializer,
        )

    @action(
        methods=["post", "patch"],
        detail=True,
        url_path="sections/interaction-and-related-projects",
    )
    def section_interaction_and_related_projects(self, request, pk=None):
        return self._handle_section(
            request,
            related_name="interactionAndRelatedProjects",
            update_serializer_class=ProjectProgrammeInteractionAndRelatedProjectsUpdateSerializer,
            get_serializer_class=ProjectProgrammeInteractionAndRelatedProjectsGetSerializer,
        )

    @action(methods=["post", "patch"], detail=True, url_path="sections/other-attachments")
    def section_other_attachments(self, request, pk=None):
        return self._handle_section(
            request,
            related_name="otherAttachments",
            update_serializer_class=ProjectProgrammeOtherAttachmentsUpdateSerializer,
            get_serializer_class=ProjectProgrammeOtherAttachmentsGetSerializer,
        )

    @action(methods=["post"], detail=True, url_path="sections/links")
    def section_links(self, request, pk=None):
        # get_object() resolves programme and runs object-level permission checks
        programme = self.get_object()
        serializer = ProjectProgrammeLinkUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        section_instance = self._get_section_instance_for_link(
            serializer.validated_data["contentType"],
            serializer.validated_data["objectId"],
        )
        if not self._section_belongs_to_programme(section_instance, programme):
            return Response({"detail": self.NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)

        serializer.save()
        return Response(
            ProjectProgrammeLinkGetSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        methods=["patch", "delete"],
        detail=True,
        url_path=r"sections/links/(?P<link_id>[^/.]+)",
    )
    def section_link_detail(self, request, pk=None, link_id=None):
        # get_object() resolves programme and runs object-level permission checks
        programme = self.get_object()
        try:
            link = ProjectProgrammeLink.objects.get(id=link_id)
        except ProjectProgrammeLink.DoesNotExist:
            return Response({"detail": self.NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)

        if not self._section_belongs_to_programme(link.sectionObject, programme):
            return Response({"detail": self.NOT_FOUND_DETAIL}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "DELETE":
            link.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = ProjectProgrammeLinkUpdateSerializer(link, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            ProjectProgrammeLinkGetSerializer(serializer.instance).data,
            status=status.HTTP_200_OK,
        )
