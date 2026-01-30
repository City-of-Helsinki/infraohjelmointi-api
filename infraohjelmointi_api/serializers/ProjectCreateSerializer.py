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
from infraohjelmointi_api.utils.project_class_utils import get_programmer_from_hierarchy
from infraohjelmointi_api.serializers import (
    BaseMeta,
    PersonSerializer,
)
from infraohjelmointi_api.serializers.ProjectProgrammerSerializer import ProjectProgrammerSerializer
from infraohjelmointi_api.serializers.BudgetItemSerializer import BudgetItemSerializer
from infraohjelmointi_api.serializers.ConstructionPhaseDetailSerializer import (
    ConstructionPhaseDetailSerializer,
)
from infraohjelmointi_api.serializers.ConstructionProcurementMethodSerializer import (
    ConstructionProcurementMethodSerializer,
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


class ProjectCreateSerializer(ProjectWithFinancesSerializer):
    projectReadiness = serializers.SerializerMethodField()
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
        # removed constructionPhaseDetail validator due to inconsistencies in imported data
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
            ConstructionEndYearValidator(),
            PlanningStartYearValidator(),
            ProgrammedValidator(),
            LockedFieldsValidator(),
        ]

    def get_pw_folder_link(self, project: Project):
        if project.hkrId is None:
            return None
        # Initializing the service here instead of when first defining the variable in the class body
        # Because on app startup, before DB tables are created, Serializer gets initialized and
        # causes the initialization of ProjectWiseService which calls the DB
        if self.projectWiseService is None:
            self.projectWiseService = ProjectWiseService()

        try:
            pwInstanceId = self.projectWiseService.get_project_from_pw(
                id=project.hkrId
            ).get("instanceId", None)
            return env("PW_PROJECT_FOLDER_LINK").format(pwInstanceId)
        except (
            PWProjectNotFoundError,
            PWProjectResponseError,
        ):
            return None

    def get_projectReadiness(self, obj: Project) -> int:
        return obj.projectReadiness()
    def _get_default_programmer_with_fallback(self, project_class):
        """
        Get default programmer with hierarchical fallback logic.
        Uses shared utility with cycle detection.
        """
        return get_programmer_from_hierarchy(project_class)

    def run_pre_create_update_validation(self, data: dict, instance=None):
        # remove projectId as it does not exist on the Project model
        data.pop("projectId", None)

        # Set default programmer from project class if one is selected and no programmer is set
        # Uses hierarchical fallback: check parent classes if current class has no default
        project_class = data.get("projectClass", None)

        # Only set default programmer if:
        # 1. We have a project class
        # 2. No programmer is being explicitly set in this request
        # 3. For updates: the existing project doesn't already have a programmer
        should_set_default = (
            project_class and
            not data.get("personProgramming", None) and
            (instance is None or instance.personProgramming is None)
        )

        if should_set_default:
            programmer = self._get_default_programmer_with_fallback(project_class)
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

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["phase"] = (
            ProjectPhaseSerializer(instance.phase).data
            if instance.phase != None
            else None
        )
        rep["area"] = (
            ProjectAreaSerializer(instance.area).data if instance.area != None else None
        )

        rep["type"] = (
            ProjectTypeSerializer(instance.type).data if instance.type != None else None
        )
        rep["typeQualifier"] = (
            ProjectTypeQualifierSerializer(instance.typeQualifier).data
            if instance.typeQualifier != None
            else None
        )
        rep["priority"] = (
            ProjectPrioritySerializer(instance.priority).data
            if instance.priority != None
            else None
        )
        rep["siteId"] = (
            BudgetItemSerializer(instance.siteId).data
            if instance.siteId != None
            else None
        )
        rep["projectSet"] = (
            ProjectSetCreateSerializer(instance.projectSet).data
            if instance.projectSet != None
            else None
        )
        rep["personPlanning"] = (
            PersonSerializer(instance.personPlanning).data
            if instance.personPlanning != None
            else None
        )
        rep["personProgramming"] = (
            ProjectProgrammerSerializer(instance.personProgramming).data
            if instance.personProgramming != None
            else None
        )
        rep["personConstruction"] = (
            PersonSerializer(instance.personConstruction).data
            if instance.personConstruction != None
            else None
        )
        rep["category"] = (
            ProjectCategorySerializer(instance.category).data
            if instance.category != None
            else None
        )
        rep["riskAssessment"] = (
            ProjectRiskSerializer(instance.riskAssessment).data
            if instance.riskAssessment != None
            else None
        )
        rep["constructionPhaseDetail"] = (
            ConstructionPhaseDetailSerializer(instance.constructionPhaseDetail).data
            if instance.constructionPhaseDetail != None
            else None
        )
        rep["constructionProcurementMethod"] = (
            ConstructionProcurementMethodSerializer(instance.constructionProcurementMethod).data
            if instance.constructionProcurementMethod != None
            else None
        )
        rep["constructionPhase"] = (
            ConstructionPhaseSerializer(instance.constructionPhase).data
            if instance.constructionPhase != None
            else None
        )
        rep["planningPhase"] = (
            PlanningPhaseSerializer(instance.planningPhase).data
            if instance.planningPhase != None
            else None
        )
        rep["projectQualityLevel"] = (
            ProjectQualityLevelSerializer(instance.projectQualityLevel).data
            if instance.projectQualityLevel != None
            else None
        )
        rep["responsibleZone"] = (
            ProjectResponsibleZoneSerializer(instance.responsibleZone).data
            if instance.responsibleZone != None
            else None
        )
        rep["budgetOverrunReason"] = (
            BudgetOverrunReasonSerializer(instance.budgetOverrunReason).data
            if instance.budgetOverrunReason != None
            else None
        )
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

