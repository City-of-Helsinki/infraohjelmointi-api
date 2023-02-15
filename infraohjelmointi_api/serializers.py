from .models import (
    ProjectType,
    Project,
    Person,
    ProjectSet,
    ProjectArea,
    BudgetItem,
    Task,
    ProjectPhase,
    ProjectPriority,
    TaskStatus,
    ConstructionPhaseDetail,
    ProjectCategory,
    ProjectRisk,
    ConstructionPhase,
    PlanningPhase,
    ProjectClass,
    ProjectQualityLevel,
    ProjectLocation,
    Note,
    ResponsibleZone,
    ProjectHashTag,
    ProjectGroup,
    ProjectLock,
)
from rest_framework import serializers
from django.db.models import Q
from overrides import override
from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator


class BaseMeta:
    exclude = ["createdDate", "updatedDate"]


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class ProjectLockSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectLock

    @override
    def create(self, validated_data):
        """
        Overriding the create method to validate
        if a project is already locked
        """
        project = validated_data.get("project", None)
        if project.lock.all().count() > 0:
            raise serializers.ValidationError(
                "Project: {} with id: {} has an already existing lock record with id: {} and lockType: {}".format(
                    project.name,
                    project.id,
                    project.lock.get(project=project).id,
                    project.lock.get(project=project).lockType,
                )
            )
        print(validated_data)
        if validated_data.get("lockedBy", None) is not None and (
            validated_data.get("lockType", None) is None
            or validated_data.get("lockType", None) is ""
        ):
            print(validated_data["lockType"])
            validated_data["lockType"] = "person"
        return super(ProjectLockSerializer, self).create(validated_data)


class ProjectGroupSerializer(DynamicFieldsModelSerializer):
    projects = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False, allow_empty=True
    )

    def validate_projects(self, projectIds):
        """
        Check that project doesn't already belong to a group
        """

        if projectIds is not None and len(projectIds) > 0:
            for projectId in projectIds:
                project = get_object_or_404(Project, pk=projectId)
                if project.projectGroup is not None:
                    raise serializers.ValidationError(
                        "Project: {} with id: {} already belongs to the group: {} with id: {}".format(
                            project.name,
                            projectId,
                            project.projectGroup.name,
                            project.projectGroup_id,
                        )
                    )
        return projectIds

    class Meta(BaseMeta):
        model = ProjectGroup
        validators = [
            UniqueTogetherValidator(
                queryset=ProjectGroup.objects.all(),
                fields=["name", "classRelation", "districtRelation"],
            ),
        ]

    @override
    def create(self, validated_data):
        projectIds = validated_data.pop("projects", None)
        projectGroup = self.Meta.model.objects.create(**validated_data)
        if projectIds is not None and len(projectIds) > 0:
            for projectId in projectIds:
                project = get_object_or_404(Project, pk=projectId)
                project.projectGroup = projectGroup
                project.save()

        return projectGroup


class ProjectHashtagSerializer(DynamicFieldsModelSerializer):
    class Meta(BaseMeta):
        model = ProjectHashTag


class ProjectLocationSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectLocation


class ProjectClassSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectClass


class ProjectQualityLevelSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectQualityLevel


class PlanningPhaseSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = PlanningPhase


class ConstructionPhaseSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ConstructionPhase


class ProjectRiskSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectRisk


class ProjectCategorySerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectCategory


class ConstructionPhaseDetailSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ConstructionPhaseDetail


class TaskStatusSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = TaskStatus


class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectPhase


class ProjectPrioritySerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectPriority


class PersonSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = Person


class NotePersonSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "firstName", "lastName")
        model = Person


class NoteHistorySerializer(serializers.ModelSerializer):
    updatedBy = NotePersonSerializer(read_only=True)

    class Meta:
        model = Note.history.model
        fields = "__all__"


class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectType


class BudgetItemSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = BudgetItem


class ProjectAreaSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectArea
        exclude = ["createdDate", "updatedDate", "location"]


class ProjectResponsibleZoneSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ResponsibleZone


class ProjectSetGetSerializer(serializers.ModelSerializer):
    sapProjects = serializers.SerializerMethodField()
    sapNetworks = serializers.SerializerMethodField()
    phase = ProjectPhaseSerializer(read_only=True)

    class Meta(BaseMeta):
        model = ProjectSet

    def get_sapNetworks(self, obj):
        return [
            network
            for obj in obj.project_set.all()
            .filter(~Q(sapNetwork=None))
            .values("sapNetwork")
            for network in obj["sapNetwork"]
        ]

    def get_sapProjects(self, obj):
        return [
            project
            for obj in obj.project_set.all()
            .filter(~Q(sapNetwork=None))
            .values("sapProject")
            for project in obj["sapProject"]
        ]


class ProjectSetCreateSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectSet


class ProjectGetSerializer(DynamicFieldsModelSerializer):
    projectReadiness = serializers.SerializerMethodField()
    projectSet = ProjectSetCreateSerializer(read_only=True)
    siteId = BudgetItemSerializer(read_only=True)
    area = ProjectAreaSerializer(read_only=True)
    type = ProjectTypeSerializer(read_only=True)
    priority = ProjectPrioritySerializer(read_only=True)
    phase = ProjectPhaseSerializer(read_only=True)
    personPlanning = PersonSerializer(read_only=True)
    personProgramming = PersonSerializer(read_only=True)
    personConstruction = PersonSerializer(read_only=True)
    estPlanningStart = serializers.DateField(format="%d.%m.%Y")
    estPlanningEnd = serializers.DateField(format="%d.%m.%Y")
    category = ProjectCategorySerializer(read_only=True)
    constructionPhaseDetail = ConstructionPhaseDetailSerializer(read_only=True)
    riskAssessment = ProjectRiskSerializer(read_only=True)
    estConstructionStart = serializers.DateField(format="%d.%m.%Y")
    estConstructionEnd = serializers.DateField(format="%d.%m.%Y")
    presenceStart = serializers.DateField(format="%d.%m.%Y")
    presenceEnd = serializers.DateField(format="%d.%m.%Y")
    visibilityStart = serializers.DateField(format="%d.%m.%Y")
    visibilityEnd = serializers.DateField(format="%d.%m.%Y")
    constructionPhase = ConstructionPhaseSerializer(read_only=True)
    planningPhase = PlanningPhaseSerializer(read_only=True)
    projectQualityLevel = ProjectQualityLevelSerializer(read_only=True)
    responsibleZone = ProjectResponsibleZoneSerializer(read_only=True)

    class Meta(BaseMeta):
        model = Project

    def get_projectReadiness(self, obj):
        return obj.projectReadiness()


class ProjectCreateSerializer(serializers.ModelSerializer):
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

    class Meta(BaseMeta):
        model = Project

    def get_projectReadiness(self, obj):
        return obj.projectReadiness()

    @override
    def create(self, validated_data):
        """
        Overriding the create method to populate ProjectLockStatus Table
        with appropriate lock status based on the phase
        """
        newPhase = validated_data.get("phase", None)
        project = super(ProjectCreateSerializer, self).create(validated_data)
        if newPhase is not None and newPhase.value == "construction":
            project.lock.create(lockType="status_construction", lockedBy=None)

        return project

    @override
    def update(self, instance, validated_data):
        """
        Overriding the update method to populate ProjectLockStatus Table
        with appropriate lock status based on the phase and validating if
        locked fields are not being updated
        """
        # Check if project is locked and any locked fields are not being updated
        if instance.lock.all().count() > 0:
            phase = validated_data.get("phase", None)
            planningStartYear = validated_data.get("planningStartYear", None)
            estPlanningStart = validated_data.get("estPlanningStart", None)
            constructionEndYear = validated_data.get("constructionEndYear", None)
            estConstructionEnd = validated_data.get("estConstructionEnd", None)
            programmed = validated_data.get("programmed", None)
            projectClass = validated_data.get("projectClas", None)
            projectLocation = validated_data.get("projectLocation", None)
            siteId = validated_data.get("siteId", None)
            realizedCost = validated_data.get("realizedCost", None)
            budgetOverrunAmount = validated_data.get("budgetOverrunAmount", None)
            budgetForecast1CurrentYear = validated_data.get(
                "budgetForecast1CurrentYear", None
            )
            budgetForecast2CurrentYear = validated_data.get(
                "budgetForecast2CurrentYear", None
            )
            budgetForecast3CurrentYear = validated_data.get(
                "budgetForecast3CurrentYear", None
            )
            budgetForecast4CurrentYear = validated_data.get(
                "budgetForecast4CurrentYear", None
            )
            budgetProposalCurrentYearPlus1 = validated_data.get(
                "budgetProposalCurrentYearPlus1", None
            )
            budgetProposalCurrentYearPlus2 = validated_data.get(
                "budgetProposalCurrentYearPlus2", None
            )
            preliminaryCurrentYearPlus3 = validated_data.get(
                "preliminaryCurrentYearPlus3", None
            )
            preliminaryCurrentYearPlus4 = validated_data.get(
                "preliminaryCurrentYearPlus4", None
            )
            preliminaryCurrentYearPlus5 = validated_data.get(
                "preliminaryCurrentYearPlus5", None
            )
            preliminaryCurrentYearPlus6 = validated_data.get(
                "preliminaryCurrentYearPlus6", None
            )
            preliminaryCurrentYearPlus7 = validated_data.get(
                "preliminaryCurrentYearPlus7", None
            )
            preliminaryCurrentYearPlus8 = validated_data.get(
                "preliminaryCurrentYearPlus8", None
            )
            preliminaryCurrentYearPlus9 = validated_data.get(
                "preliminaryCurrentYearPlus9", None
            )
            preliminaryCurrentYearPlus10 = validated_data.get(
                "preliminaryCurrentYearPlus10", None
            )
            if (
                phase is not None
                or planningStartYear is not None
                or estPlanningStart is not None
                or constructionEndYear is not None
                or estConstructionEnd is not None
                or programmed is not None
                or projectClass is not None
                or projectLocation is not None
                or siteId is not None
                or budgetForecast1CurrentYear is not None
                or budgetForecast2CurrentYear is not None
                or budgetForecast3CurrentYear is not None
                or budgetForecast4CurrentYear is not None
                or budgetProposalCurrentYearPlus1 is not None
                or budgetProposalCurrentYearPlus2 is not None
                or preliminaryCurrentYearPlus3 is not None
                or preliminaryCurrentYearPlus4 is not None
                or preliminaryCurrentYearPlus5 is not None
                or preliminaryCurrentYearPlus6 is not None
                or preliminaryCurrentYearPlus7 is not None
                or preliminaryCurrentYearPlus8 is not None
                or preliminaryCurrentYearPlus9 is not None
                or preliminaryCurrentYearPlus10 is not None
                or realizedCost is not None
                or budgetOverrunAmount is not None
            ):
                raise serializers.ValidationError(
                    "The following fields cannot be updated when the project is locked,"
                    "'phase', 'planningStartYear', 'estPlanningStart', 'constructionEndYear',"
                    "'estConstructionEnd', 'programmed', 'projectClass', 'projectLocation',"
                    "'siteId', 'realizedCost', 'budgetOverrunAmount', 'budgetForecast1CurrentYear', 'budgetForecast2CurrentYear',"
                    "'budgetForecast3CurrentYear', 'budgetForecast4CurrentYear', 'budgetProposalCurrentYearPlus1',"
                    "'budgetProposalCurrentYearPlus2', 'preliminaryCurrentYearPlus3', 'preliminaryCurrentYearPlus4',"
                    "'preliminaryCurrentYearPlus5', 'preliminaryCurrentYearPlus6', 'preliminaryCurrentYearPlus7', 'preliminaryCurrentYearPlus8',"
                    "'preliminaryCurrentYearPlus9', 'preliminaryCurrentYearPlus10'"
                )
        else:
            newPhase = validated_data.get("phase", None)
            if newPhase is not None and newPhase.value == "construction":
                instance.lock.create(lockType="status_construction", lockedBy=None)
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


class PersonSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = Person


class TaskSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = Task


class NoteGetSerializer(serializers.ModelSerializer):
    updatedBy = NotePersonSerializer(read_only=True)
    deleted = serializers.ReadOnlyField()

    class Meta(BaseMeta):
        exclude = ["updatedDate"]
        model = Note


class ProjectNoteGetSerializer(serializers.ModelSerializer):
    updatedBy = NotePersonSerializer(read_only=True)
    deleted = serializers.ReadOnlyField()

    class Meta(BaseMeta):
        exclude = ["updatedDate"]
        model = Note

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["history"] = NoteHistorySerializer(instance.history.all(), many=True).data

        return rep


class NoteCreateSerializer(serializers.ModelSerializer):
    deleted = serializers.ReadOnlyField()

    class Meta(BaseMeta):
        exclude = ["updatedDate"]
        model = Note

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["updatedBy"] = (
            NotePersonSerializer(instance.updatedBy).data
            if instance.updatedBy != None
            else None
        )

        return rep


class NoteUpdateSerializer(serializers.ModelSerializer):
    deleted = serializers.ReadOnlyField()

    class Meta(BaseMeta):
        exclude = ["updatedDate"]
        model = Note

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)

        rep["updatedBy"] = (
            NotePersonSerializer(instance.updatedBy).data
            if instance.updatedBy != None
            else None
        )

        rep["history"] = (
            NoteHistorySerializer(instance.history.all(), many=True).data
            if instance.history
            else None
        )

        return rep
