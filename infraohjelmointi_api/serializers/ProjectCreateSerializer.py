from infraohjelmointi_api.models import (
    Project,
    ProjectClass,
    ProjectLocation,
    ProjectPhase,
)
from infraohjelmointi_api.serializers import BaseMeta, PersonSerializer
from infraohjelmointi_api.serializers.BudgetItemSerializer import BudgetItemSerializer
from infraohjelmointi_api.serializers.ConstructionPhaseDetailSerializer import (
    ConstructionPhaseDetailSerializer,
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
from infraohjelmointi_api.validators.ProjectValidators import (
    ConstructionEndYearValidator,
    ConstructionPhaseDetailValidator,
    EstConstructionEndValidator,
    EstConstructionStartValidator,
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


class FinancialSumSerializer(serializers.ModelSerializer):
    finances = serializers.SerializerMethodField(method_name="get_finance_sums")

    def get_finance_sums(self, instance):
        _type = instance._meta.model.__name__
        year = int(self.context.get("finance_year", date.today().year))
        relatedProjects = self.get_related_projects(instance=instance, _type=_type)
        summedFinances = relatedProjects.aggregate(
            year0_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year),
            ),
            year1_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 1),
            ),
            year2_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 2),
            ),
            year3_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 3),
            ),
            year4_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 4),
            ),
            year5_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 5),
            ),
            year6_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 6),
            ),
            year7_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 7),
            ),
            year8_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 8),
            ),
            year9_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 9),
            ),
            year10_plannedBudget=Sum(
                "finances__value",
                default=0,
                filter=Q(finances__year=year + 10),
            ),
            budgetOverrunAmount=Sum("budgetOverrunAmount", default=0),
        )
        if _type == "ProjectGroup":
            summedFinances["projectBudgets"] = relatedProjects.aggregate(
                projectBudgets=Sum("costForecast", default=0)
            )["projectBudgets"]
        summedFinances["year"] = year
        summedFinances["year0"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year0_plannedBudget")),
        }
        summedFinances["year1"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year1_plannedBudget")),
        }
        summedFinances["year2"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year2_plannedBudget")),
        }
        summedFinances["year3"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year3_plannedBudget")),
        }
        summedFinances["year4"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year4_plannedBudget")),
        }
        summedFinances["year5"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year5_plannedBudget")),
        }
        summedFinances["year6"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year6_plannedBudget")),
        }
        summedFinances["year7"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year7_plannedBudget")),
        }
        summedFinances["year8"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year8_plannedBudget")),
        }
        summedFinances["year9"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year9_plannedBudget")),
        }
        summedFinances["year10"] = {
            "frameBudget": 0,
            "plannedBudget": int(summedFinances.pop("year10_plannedBudget")),
        }

        return summedFinances

    def get_related_projects(self, instance, _type) -> list[Project]:
        if _type == "ProjectLocation":
            if instance.parent is None:
                return Project.objects.filter(
                    Q(projectLocation=instance)
                    | Q(projectLocation__parent=instance)
                    | Q(projectLocation__parent__parent=instance)
                ).prefetch_related("finances")
            return Project.objects.none()
        if _type == "ProjectClass":
            return Project.objects.filter(
                projectClass__path__startswith=instance.path
            ).prefetch_related("finances")

        if _type == "ProjectGroup":
            return ProjectService.find_by_group_id(
                group_id=instance.id
            ).prefetch_related("finances")

        return Project.objects.none()


class ProjectFinancialSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectFinancial
        exclude = ["createdDate", "updatedDate", "id"]
        validators = [
            UniqueTogetherValidator(
                queryset=ProjectFinancial.objects.all(),
                fields=["year", "project"],
            ),
        ]

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep.pop("project")
        return rep

    @override
    def update(self, instance, validated_data):
        # Check if project is locked and any locked fields are not being updated
        year = self.context.get("finance_year", date.today().year)
        if year is None:
            year = date.today().year
        yearToFieldMapping = (
            ProjectFinancialService.get_year_to_financial_field_names_mapping(
                start_year=year
            )
        )
        if hasattr(instance.project, "lock"):
            lockedFields = [
                "value",
            ]
            for field in lockedFields:
                if validated_data.get(field, None) is not None:
                    raise serializers.ValidationError(
                        "The field {} cannot be modified when the project is locked".format(
                            yearToFieldMapping[instance.year]
                        )
                    )

        return super(ProjectFinancialSerializer, self).update(instance, validated_data)


class ProjectWithFinancesSerializer(serializers.ModelSerializer):
    finances = serializers.SerializerMethodField()

    def get_finances(self, project):
        """
        A function used to get financial fields of a project using context passed to the serializer.
        If no year is passed to the serializer using either the project id or finance_year as key
        the current year is used as the default.
        """

        year = self.context.get(
            str(project.id), self.context.get("finance_year", date.today().year)
        )
        if year is None:
            year = date.today().year
        year = int(year)
        yearToFieldMapping = (
            ProjectFinancialService.get_year_to_financial_field_names_mapping(
                start_year=year
            )
        )
        queryset = ProjectFinancialService.find_by_project_id_and_year_range(
            project_id=project.id, year_range=range(year, year + 11)
        )
        allFinances = ProjectFinancialSerializer(queryset, many=True).data
        serializedFinances = {"year": year}
        for finance in allFinances:
            serializedFinances[yearToFieldMapping[finance["year"]]] = finance["value"]
            # pop out already mapped keys
            yearToFieldMapping.pop(finance["year"])
        # remaining year keys which had no data in DB
        for yearKey in yearToFieldMapping.keys():
            serializedFinances[yearToFieldMapping[yearKey]] = "0.00"

        return serializedFinances

    class Meta(BaseMeta):
        model = Project


class UpdateListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):
        instance_hash = {index: instance for index, instance in enumerate(instances)}

        result = [
            self.child.update(instance_hash[index], attrs)
            for index, attrs in enumerate(validated_data)
        ]

        return result


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
            EstConstructionEndValidator(),
            ProjectClassValidator(),
            ProjectLocationValidator(),
            ProjectPhaseValidator(),
            ConstructionPhaseDetailValidator(),
            PlanningStartYearValidator(),
            ConstructionEndYearValidator(),
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
        except (PWProjectNotFoundError, PWProjectResponseError):
            return None

    def get_projectReadiness(self, obj: Project) -> int:
        return obj.projectReadiness()

    @override
    def create(self, validated_data):
        phase = validated_data.get("phase", None)
        if phase is not None and phase.value == "programming":
            validated_data["programmed"] = True

        if phase is not None and (
            phase.value == "completed"
            or phase.value == "warrantyPeriod"
            or phase.value == "proposal"
        ):
            validated_data["programmed"] = False

        project = super(ProjectCreateSerializer, self).create(validated_data)

        return project

    @override
    def update(self, instance, validated_data):
        phase = validated_data.get("phase", None)

        if phase is not None and phase.value == "programming":
            validated_data["programmed"] = True

        if phase is not None and (
            phase.value == "completed"
            or phase.value == "warrantyPeriod"
            or phase.value == "proposal"
        ):
            validated_data["programmed"] = False

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
            PersonSerializer(instance.personProgramming).data
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
        return rep
