import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.db import transaction
from overrides import override
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
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
from infraohjelmointi_api.permissions import (
    get_project_programme_contributor_group_name,
    get_restricted_programmer_group_name,
)
from infraohjelmointi_api.services.ProjectPersonAuthorizationService import (
    ProjectPersonAuthorizationService,
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
    SECTION_RELATIONS = {
        "basicinfo": "basicInfo",
        "designcriteria": "designCriteria",
        "trafficplanningcriteria": "trafficPlanningCriteria",
        "urbanspacingplanningcriteria": "urbanSpacingPlanningCriteria",
        "maintenanceneeds": "maintenanceNeeds",
        "interactionandrelatedprojects": "interactionAndRelatedProjects",
        "otherattachments": "otherAttachments",
    }
    REVIEWER_GROUPS = {
        "sg_kymp_sso_io_koordinaattorit",
        "sg_kymp_sso_io_ohjelmoijat",
        "sg_kymp_sso_io_projektialueiden_ohjelmoijat",
    }
    COMMISSIONING_MANAGER_GROUP = "sg_kymp_sso_io_projektipaallikot"
    ADMIN_GROUP = "sg_kymp_sso_io_admin"

    @override
    def get_queryset(self):
        queryset = ProjectProgramme.objects.all()
        if self.action in ["list", "retrieve", "get_by_project", "transitions", "section_transitions"]:
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

    def _normalize_section_key(self, section_key):
        return "".join(char for char in str(section_key or "") if char.isalnum()).lower()

    def _resolve_section_relation_name(self, section_key):
        normalized_key = self._normalize_section_key(section_key)
        return self.SECTION_RELATIONS.get(normalized_key)

    def _get_user_group_names(self, user):
        if not user or not getattr(user, "is_authenticated", False):
            return set()
        return set(user.ad_groups.all().values_list("name", flat=True))

    def _matches_programmer_name_from_email(self, user_email, project_programmer):
        if not user_email or not project_programmer:
            return False

        local_part = user_email.split("@")[0]
        name_parts = [part.strip().lower() for part in local_part.split(".") if part.strip()]
        if len(name_parts) < 2:
            return False

        first_name = (project_programmer.firstName or "").strip().lower()
        last_name = (project_programmer.lastName or "").strip().lower()
        return name_parts[0] == first_name and name_parts[1] == last_name

    def _is_responsible_for_project_programme(self, user, project):
        if not user or not getattr(user, "is_authenticated", False) or not project:
            return False

        if ProjectPersonAuthorizationService.is_person_planning_for_project(user, project):
            return True

        if ProjectPersonAuthorizationService.is_person_construction_for_project(user, project):
            return True

        project_programmer = getattr(project, "personProgramming", None)
        programmer_person = getattr(project_programmer, "person", None)
        if ProjectPersonAuthorizationService.is_matching_project_person_email(
            user, programmer_person
        ):
            return True

        user_email = (getattr(user, "email", "") or "").strip().lower()
        if not user_email:
            return False

        if self._matches_programmer_name_from_email(user_email, project_programmer):
            return True

        project_set = getattr(project, "projectSet", None)
        project_set_responsible = getattr(project_set, "responsiblePerson", None)
        if ProjectPersonAuthorizationService.is_matching_project_person_email(
            user, project_set_responsible
        ):
            return True

        if project.otherPersons.filter(email__iexact=user_email).exists():
            return True

        if project.favPersons.filter(email__iexact=user_email).exists():
            return True

        return False

    def _assert_can_create_programme(self, request, project):
        user = self._get_authenticated_user(request)
        group_names = self._get_user_group_names(user)
        if self.ADMIN_GROUP in group_names:
            return

        if self._is_responsible_for_project_programme(user, project):
            return

        raise PermissionDenied(
            "Only the responsible project programme person can create a project programme."
        )

    def _assert_can_edit_or_complete(self, request, project):
        user = self._get_authenticated_user(request)
        group_names = self._get_user_group_names(user)
        if self.ADMIN_GROUP in group_names:
            return

        if self.COMMISSIONING_MANAGER_GROUP in group_names:
            raise PermissionDenied(
                "Commissioning managers can only return a project programme to DRAFT."
            )

        reviewer_groups = {*self.REVIEWER_GROUPS, get_restricted_programmer_group_name()}
        if group_names.intersection(reviewer_groups):
            return

        if get_project_programme_contributor_group_name() in group_names:
            return

        if self._is_responsible_for_project_programme(user, project):
            return

        raise PermissionDenied(
            "You do not have permission to edit or complete this project programme."
        )

    def _assert_can_return_to_draft(self, request):
        user = self._get_authenticated_user(request)
        group_names = self._get_user_group_names(user)
        if self.ADMIN_GROUP in group_names:
            return

        reviewer_groups = {*self.REVIEWER_GROUPS, get_restricted_programmer_group_name()}
        if group_names.intersection(reviewer_groups):
            return

        if self.COMMISSIONING_MANAGER_GROUP in group_names:
            return

        raise PermissionDenied(
            "Only reviewers or commissioning managers can return a project programme to DRAFT."
        )

    def _validate_for_complete(self, instance, entity_name):
        try:
            instance.full_clean()
        except DjangoValidationError as error:
            raise ValidationError(
                {
                    "detail": f"Cannot mark {entity_name} as COMPLETE.",
                    "errors": error.message_dict,
                }
            )

    def _validate_programme_and_draft_sections_for_complete(self, programme):
        self._validate_for_complete(programme, "project programme")

        draft_sections = []
        for relation_name in self.SECTION_RELATIONS.values():
            if not hasattr(programme, relation_name):
                continue

            section = getattr(programme, relation_name)
            if section.status != "DRAFT":
                continue

            self._validate_for_complete(section, f"section '{relation_name}'")
            draft_sections.append(section)

        return draft_sections

    def _get_section_instance(self, programme, section_key):
        relation_name = self._resolve_section_relation_name(section_key)
        if not relation_name:
            return None, None

        if not hasattr(programme, relation_name):
            return relation_name, None

        return relation_name, getattr(programme, relation_name)

    @override
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = serializer.validated_data.get("project")
        existing = ProjectProgramme.objects.filter(project=project).first()
        if existing is not None:
            return Response(
                {
                    "detail": "Project programme already exists for this project.",
                    "id": str(existing.id),
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            self.perform_create(serializer)
        except IntegrityError:
            existing_after_race = ProjectProgramme.objects.filter(project=project).first()
            if existing_after_race is not None:
                return Response(
                    {
                        "detail": "Project programme already exists for this project.",
                        "id": str(existing_after_race.id),
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            raise

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @override
    def perform_create(self, serializer):
        project = serializer.validated_data.get("project")
        self._assert_can_create_programme(self.request, project)

        user = self._get_authenticated_user(self.request)
        if user:
            serializer.save(createdBy=user, updatedBy=user)
            return
        serializer.save()

    @override
    def perform_update(self, serializer):
        project = getattr(serializer.instance, "project", None)
        self._assert_can_edit_or_complete(self.request, project)

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

        if requested_status == "DRAFT":
            self._assert_can_return_to_draft(request)
        else:
            self._assert_can_edit_or_complete(request, instance.project)

        user = self._get_authenticated_user(request)
        with transaction.atomic():
            draft_sections = []
            if requested_status == "COMPLETE":
                draft_sections = self._validate_programme_and_draft_sections_for_complete(
                    instance
                )

            instance.status = requested_status
            if user:
                instance.updatedBy = user
            instance.save()

            for section in draft_sections:
                section.status = "COMPLETE"
                if user:
                    section.updatedBy = user
                section.save()

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

    @action(
        methods=["post"],
        detail=True,
        url_path=r"sections/(?P<section_key>[^/.]+)/transitions",
    )
    def section_transitions(self, request, pk=None, section_key=None):
        programme = self.get_object()
        relation_name, section_instance = self._get_section_instance(programme, section_key)

        if not relation_name:
            return Response(
                {"detail": "Unknown section key."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not section_instance:
            return Response(
                {
                    "detail": f"Section '{relation_name}' was not found for this project programme."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProjectProgrammeStatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_status = serializer.validated_data["to"]
        if section_instance.status == requested_status:
            return Response(
                {"detail": "Section is already in the requested status."},
                status=status.HTTP_409_CONFLICT,
            )

        if programme.status != "DRAFT":
            return Response(
                {
                    "detail": (
                        "Sections can only be transitioned when the project programme "
                        "is in DRAFT status."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        if requested_status == "DRAFT":
            self._assert_can_return_to_draft(request)
        else:
            self._assert_can_edit_or_complete(request, programme.project)

        if requested_status == "COMPLETE":
            self._validate_for_complete(section_instance, f"section '{relation_name}'")

        user = self._get_authenticated_user(request)
        section_instance.status = requested_status
        if user:
            section_instance.updatedBy = user
        section_instance.save()

        return Response(
            {
                "section": relation_name,
                "currentStatus": section_instance.status,
            },
            status=status.HTTP_200_OK,
        )
