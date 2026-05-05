from os import path
import logging
from infraohjelmointi_api.models import (
    Project,
)

logger = logging.getLogger("infraohjelmointi_api")
from infraohjelmointi_api.services.ProjectWiseService import (
    PWProjectNotFoundError,
    PWProjectResponseError,
    ProjectWiseService,
)
from infraohjelmointi_api.services.utils import create_comprehensive_project_data
from infraohjelmointi_api.utils.project_class_utils import (
    get_default_programmer_for_project,
)
from infraohjelmointi_api.serializers import (
    BaseMeta,
    PersonSerializer,
)
from infraohjelmointi_api.serializers.ProjectProgrammerSerializer import ProjectProgrammerSerializer
from infraohjelmointi_api.serializers.BudgetItemSerializer import BudgetItemSerializer
from infraohjelmointi_api.serializers.ProjectPhaseDetailSerializer import (
    ProjectPhaseDetailSerializer,
)
from infraohjelmointi_api.serializers.ConstructionProcurementMethodSerializer import (
    ConstructionProcurementMethodSerializer,
)
from infraohjelmointi_api.serializers.StaraProcurementReasonSerializer import (
    StaraProcurementReasonSerializer,
)
from infraohjelmointi_api.serializers.ConstructionPhaseSerializer import (
    ConstructionPhaseSerializer,
)
from infraohjelmointi_api.serializers.PlanningPhaseSerializer import (
    PlanningPhaseSerializer,
)
from infraohjelmointi_api.serializers.ProjectAreaSerializer import ProjectAreaSerializer
from infraohjelmointi_api.serializers.ProjectCategorySerializer import (
    ProjectCategorySerializer,
)
from infraohjelmointi_api.serializers.ProjectPhaseSerializer import (
    ProjectPhaseSerializer,
)
from infraohjelmointi_api.serializers.ProjectPrioritySerializer import (
    ProjectPrioritySerializer,
)
from infraohjelmointi_api.serializers.ProjectQualityLevelSerializer import (
    ProjectQualityLevelSerializer,
)
from infraohjelmointi_api.serializers.ProjectResponsibleZoneSerializer import (
    ProjectResponsibleZoneSerializer,
)
from infraohjelmointi_api.serializers.ProjectRiskSerializer import ProjectRiskSerializer
from infraohjelmointi_api.serializers.ProjectSetCreateSerializer import (
    ProjectSetCreateSerializer,
)
from infraohjelmointi_api.serializers.ProjectTypeSerializer import ProjectTypeSerializer
from infraohjelmointi_api.serializers.ProjectTypeQualifierSerializer import ProjectTypeQualifierSerializer
from infraohjelmointi_api.serializers.ProjectWithFinancesSerializer import (
    ProjectWithFinancesSerializer,
)
from infraohjelmointi_api.serializers.UpdateListSerializer import UpdateListSerializer
from infraohjelmointi_api.serializers.BudgetOverrunReasonSerializer import BudgetOverrunReasonSerializer
from infraohjelmointi_api.serializers.serializer_utils import get_pw_folder_link_for_project
from infraohjelmointi_api.validators.ProjectValidators import (
    ConstructionEndYearValidator,
    EstConstructionEndValidator,
    EstConstructionStartValidator,
    EstWarrantyPhaseStartValidator,
    EstPlanningEndValidator,
    LockedFieldsValidator,
    PlanningStartYearValidator,
    PresenceEndValidator,
    ProgrammedValidator,
    ProjectClassValidator,
    ProjectLocationValidator,
    ProjectPhaseDetailValidator,
    ProjectPhaseValidator,
    VisibilityEndValidator,
    VisibilityStartValidator,
)
from infraohjelmointi_api.validators.ProjectValidators.EstPlanningStartValidator import (
    EstPlanningStartValidator,
)
from infraohjelmointi_api.validators.ProjectValidators import PresenceStartValidator
from rest_framework import serializers
from overrides import override
import environ

env = environ.Env()
env.escape_proxy = True

if path.exists(".env"):
    env.read_env(".env")


# Distinguishes "key absent from payload" from "key set to None" so an
# explicit null clear (IO-411) is not silently replaced by the persisted
# instance value during default-programmer resolution.
_FIELD_MISSING = object()


class ProjectCreateSerializer(ProjectWithFinancesSerializer):
    projectReadiness = serializers.SerializerMethodField()
    postalCode = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    city = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    estPlanningStart = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    estPlanningEnd = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    estConstructionStart = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    estConstructionEnd = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    estWarrantyPhaseStart = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    estWarrantyPhaseEnd = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    frameEstPlanningStart = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    frameEstPlanningEnd = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    frameEstConstructionStart = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    frameEstConstructionEnd = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    frameEstWarrantyPhaseStart = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    frameEstWarrantyPhaseEnd = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    presenceStart = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    presenceEnd = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    visibilityStart = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    visibilityEnd = serializers.DateField(
        format="%d.%m.%Y",
        input_formats=["%d.%m.%Y", "iso-8601"],
        required=False,
        allow_null=True,
    )
    pwFolderLink = serializers.SerializerMethodField(method_name="get_pw_folder_link")
    projectWiseService = None
    # write only field used when updating multiple projects
    # helps during validation
    projectId = serializers.UUIDField(write_only=True, required=False)

    estFieldsRelations = [
        ("estPlanningStart", "frameEstPlanningStart"),
        ("estPlanningEnd", "frameEstPlanningEnd"),
        ("estConstructionStart", "frameEstConstructionStart"),
        ("estConstructionEnd", "frameEstConstructionEnd"),
    ]

    class Meta(BaseMeta):
        model = Project
        list_serializer_class = UpdateListSerializer
        validators = [
            EstPlanningStartValidator(),
            EstPlanningEndValidator(),
            PresenceStartValidator(),
            PresenceEndValidator(),
            VisibilityStartValidator(),
            VisibilityEndValidator(),
            EstConstructionStartValidator(),
            EstWarrantyPhaseStartValidator(),
            EstConstructionEndValidator(),
            ProjectClassValidator(),
            ProjectLocationValidator(),
            ProjectPhaseValidator(),
            ProjectPhaseDetailValidator(),
            ConstructionEndYearValidator(),
            PlanningStartYearValidator(),
            ProgrammedValidator(),
            LockedFieldsValidator(),
        ]

    def get_pw_folder_link(self, project: Project):
        return get_pw_folder_link_for_project(project, self.projectWiseService)

    def get_projectReadiness(self, obj: Project) -> int:
        return obj.projectReadiness()

    def _get_default_programmer_with_fallback(self, project_class, project_location=None):
        """Walk projectClass parents first, then projectLocation parents (IO-411)."""
        return get_default_programmer_for_project(project_class, project_location)

    def _resolve_class_and_location_for_programmer(self, data: dict, instance):
        """
        Pick the projectClass / projectLocation values fed into the
        default-programmer resolver. If a side is in ``data`` (even as
        ``None``), use it verbatim; otherwise fall back to the persisted
        instance value so the *other* side's change still has full context.
        """
        incoming_class = data.get("projectClass", _FIELD_MISSING)
        incoming_location = data.get("projectLocation", _FIELD_MISSING)

        if incoming_class is not _FIELD_MISSING:
            project_class = incoming_class
        elif instance is not None:
            project_class = getattr(instance, "projectClass", None)
        else:
            project_class = None

        if incoming_location is not _FIELD_MISSING:
            project_location = incoming_location
        elif instance is not None:
            project_location = getattr(instance, "projectLocation", None)
        else:
            project_location = None

        return project_class, project_location

    def run_pre_create_update_validation(self, data: dict, instance=None):
        # remove projectId as it does not exist on the Project model
        data.pop("projectId", None)

        # IO-411: only auto-assign personProgramming on create or on an update
        # that touches projectClass / projectLocation, and only when no
        # programmer is currently set. Explicit nulls are honoured (see the
        # resolver above) so the user's clear is never silently undone.
        request_touches_class_or_location = (
            instance is None
            or "projectClass" in data
            or "projectLocation" in data
        )
        project_class, project_location = self._resolve_class_and_location_for_programmer(
            data, instance
        )

        should_set_default = (
            request_touches_class_or_location
            and (project_class or project_location)
            and not data.get("personProgramming", None)
            and (instance is None or instance.personProgramming is None)
        )

        if should_set_default:
            programmer = self._get_default_programmer_with_fallback(
                project_class, project_location
            )
            if programmer:
                data["personProgramming"] = programmer

        phase = data.get("phase", None)
        if phase is not None and phase.value == "programming":
            data["programmed"] = True

        if phase is not None and phase.value == "proposal":
            data["programmed"] = False
        
        # IO-755: When marking project as completed, set programmed based on budget
        # Only auto-set if user hasn't explicitly provided a value
        if phase is not None and phase.value == "completed" and "programmed" not in data:
            # Check if project has budget reservations for current year
            from datetime import date
            current_year = date.today().year
            
            # If this is an update (instance exists), check its finances
            if instance:
                # Check finances for current year (both frameView types)
                has_current_year_budget = instance.finances.filter(
                    year=current_year,
                    forFrameView=False  # Only check actual budget, not frame view
                ).exclude(value=0).exclude(value__isnull=True).exists()
                
                # Set programmed based on budget existence
                data["programmed"] = has_current_year_budget
            else:
                # For new projects being created as completed (unlikely), default to False
                data["programmed"] = False

        for estDate, frameEstDate in self.estFieldsRelations:
            if data.get(estDate, None) != None and (
                instance == None
                or (
                    getattr(instance, frameEstDate, None) == None
                    and data.get(frameEstDate, None) != None
                )
            ):
                data[frameEstDate] = data.get(estDate)

        return data

    @override
    def create(self, validated_data):
        validated_data = self.run_pre_create_update_validation(data=validated_data)
        project = super(ProjectCreateSerializer, self).create(validated_data)

        # Automatic ProjectWise sync when project is created with PW ID
        self._sync_new_project_to_projectwise(project)

        return project

    @override
    def update(self, instance, validated_data):
        validated_data = self.run_pre_create_update_validation(
            data=validated_data, instance=instance
        )

        # Commented out logic for automatic locking of project if phase updated to construction
        # else:
        #     newPhase = validated_data.get("phase", None)
        #     if newPhase is not None and newPhase.value == "construction":
        #         instance.lock.create(lockType="status_construction", lockedBy=None)
        return super(ProjectCreateSerializer, self).update(instance, validated_data)

    def _serialize_optional_field(self, value, serializer_class, many=False):
        """
        Helper method to serialize optional nested fields.
        Eliminates code duplication for null-checking and serialization.
        """
        return (
            serializer_class(value, many=many).data
            if value is not None
            else None
        )

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["phase"] = self._serialize_optional_field(instance.phase, ProjectPhaseSerializer)
        rep["area"] = self._serialize_optional_field(instance.area, ProjectAreaSerializer)
        rep["type"] = self._serialize_optional_field(instance.type, ProjectTypeSerializer)
        rep["typeQualifier"] = self._serialize_optional_field(instance.typeQualifier, ProjectTypeQualifierSerializer)
        rep["priority"] = self._serialize_optional_field(instance.priority, ProjectPrioritySerializer)
        rep["siteId"] = self._serialize_optional_field(instance.siteId, BudgetItemSerializer)
        rep["projectSet"] = self._serialize_optional_field(instance.projectSet, ProjectSetCreateSerializer)
        rep["personPlanning"] = self._serialize_optional_field(instance.personPlanning, PersonSerializer)
        rep["personProgramming"] = self._serialize_optional_field(instance.personProgramming, ProjectProgrammerSerializer)
        rep["personConstruction"] = self._serialize_optional_field(instance.personConstruction, PersonSerializer)
        rep["otherPersons"] = self._serialize_optional_field(instance.otherPersons, PersonSerializer, many=True)
        rep["category"] = self._serialize_optional_field(instance.category, ProjectCategorySerializer)
        rep["riskAssessment"] = self._serialize_optional_field(instance.riskAssessment, ProjectRiskSerializer)
        rep["phaseDetail"] = self._serialize_optional_field(instance.phaseDetail, ProjectPhaseDetailSerializer)
        rep["suspendedFromPhase"] = self._serialize_optional_field(instance.suspendedFromPhase, ProjectPhaseSerializer)
        rep["constructionProcurementMethod"] = self._serialize_optional_field(instance.constructionProcurementMethod, ConstructionProcurementMethodSerializer)
        rep["staraProcurementReason"] = self._serialize_optional_field(instance.staraProcurementReason, StaraProcurementReasonSerializer)
        rep["constructionPhase"] = self._serialize_optional_field(instance.constructionPhase, ConstructionPhaseSerializer)
        rep["planningPhase"] = self._serialize_optional_field(instance.planningPhase, PlanningPhaseSerializer)
        rep["projectQualityLevel"] = self._serialize_optional_field(instance.projectQualityLevel, ProjectQualityLevelSerializer)
        rep["responsibleZone"] = self._serialize_optional_field(instance.responsibleZone, ProjectResponsibleZoneSerializer)
        rep["budgetOverrunReason"] = self._serialize_optional_field(instance.budgetOverrunReason, BudgetOverrunReasonSerializer)
        return rep

    def _sync_new_project_to_projectwise(self, project: Project):
        """
        Handle automatic ProjectWise synchronization when a new project is created with PW ID.

        Args:
            project: The newly created project instance
        """
        # Check if project was created with a PW ID
        # IO-396 requirement: Only sync programmed projects
        if project.hkrId is not None and str(project.hkrId).strip() != "" and project.programmed:
            logger.info(f"Automatic PW sync triggered for new project '{project.name}' (HKR ID: {project.hkrId})")

            try:
                # Create comprehensive data dict for automatic update
                automatic_update_data = create_comprehensive_project_data(project)
                logger.debug(f"Automatic update data includes {len(automatic_update_data)} fields: {list(automatic_update_data.keys())}")

                # Initialize ProjectWise service and sync
                project_wise_service = ProjectWiseService()
                project_wise_service.sync_project_to_pw(
                    data=automatic_update_data, project=project
                )

                logger.info(f"Successfully synced new project '{project.name}' to ProjectWise")

            except Exception as e:
                # Log detailed error
                logger.error(f"Automatic PW sync failed for new project '{project.name}' (HKR ID: {project.hkrId})")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error message: {str(e)}")
                logger.error(f"Project created successfully but PW sync failed - data may be out of sync")
                # Don't raise - allow project creation to succeed, user can retry sync with button
        else:
            if project.hkrId is None or str(project.hkrId).strip() == "":
                logger.debug(f"New project '{project.name}' created without PW ID - skipping PW sync")
            elif not project.programmed:
                logger.debug(f"New project '{project.name}' created but not programmed - skipping PW sync (IO-396 requirement)")

