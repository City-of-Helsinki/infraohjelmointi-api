from datetime import datetime
from os import path
import environ
from infraohjelmointi_api.services import ProjectFinancialService, ProjectService
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
    ProjectFinancial,
)
from django.db.models import Sum
from .services import ProjectWiseService
from .services.ProjectWiseService import PWProjectNotFoundError, PWProjectResponseError
from rest_framework.exceptions import ParseError, ValidationError
from datetime import date
from rest_framework import serializers
from django.db.models import Q
from overrides import override
from django.shortcuts import get_object_or_404
from rest_framework.validators import UniqueTogetherValidator

import logging

logger = logging.getLogger("infraohjelmointi_api")
env = environ.Env()
env.escape_proxy = True

if path.exists(".env"):
    env.read_env(".env")


class BaseMeta:
    exclude = ["createdDate"]


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


class FinancialSumSerializer(serializers.ModelSerializer):
    finances = serializers.SerializerMethodField(method_name="get_finance_sums")

    def get_finance_sums(self, instance):
        _type = instance._meta.model.__name__
        year = int(self.context.get("finance_year", date.today().year))
        relatedProjects = self.get_related_projects(instance=instance, _type=_type)
        summedFinances = relatedProjects.aggregate(
            year0_plannedBudget=Sum(
                "finances__budgetProposalCurrentYearPlus0",
                default=0,
                filter=Q(finances__year=year),
            ),
            year1_plannedBudget=Sum(
                "finances__budgetProposalCurrentYearPlus1",
                default=0,
                filter=Q(finances__year=year),
            ),
            year2_plannedBudget=Sum(
                "finances__budgetProposalCurrentYearPlus2",
                default=0,
                filter=Q(finances__year=year),
            ),
            year3_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus3",
                default=0,
                filter=Q(finances__year=year),
            ),
            year4_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus4",
                default=0,
                filter=Q(finances__year=year),
            ),
            year5_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus5",
                default=0,
                filter=Q(finances__year=year),
            ),
            year6_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus6",
                default=0,
                filter=Q(finances__year=year),
            ),
            year7_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus7",
                default=0,
                filter=Q(finances__year=year),
            ),
            year8_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus8",
                default=0,
                filter=Q(finances__year=year),
            ),
            year9_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus9",
                default=0,
                filter=Q(finances__year=year),
            ),
            year10_plannedBudget=Sum(
                "finances__preliminaryCurrentYearPlus10",
                default=0,
                filter=Q(finances__year=year),
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
        if hasattr(instance.project, "lock"):
            lockedFields = [
                "budgetProposalCurrentYearPlus0",
                "budgetProposalCurrentYearPlus1",
                "budgetProposalCurrentYearPlus2",
                "preliminaryCurrentYearPlus3",
                "preliminaryCurrentYearPlus4",
                "preliminaryCurrentYearPlus5",
                "preliminaryCurrentYearPlus6",
                "preliminaryCurrentYearPlus7",
                "preliminaryCurrentYearPlus8",
                "preliminaryCurrentYearPlus9",
                "preliminaryCurrentYearPlus10",
            ]
            for field in lockedFields:
                if validated_data.get(field, None) is not None:
                    raise serializers.ValidationError(
                        "The field {} cannot be modified when the project is locked".format(
                            field
                        )
                    )

        return super(ProjectFinancialSerializer, self).update(instance, validated_data)


class ProjectLockSerializer(serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectLock


class SearchResultSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    hashTags = serializers.SerializerMethodField()
    phase = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()
    programmed = serializers.SerializerMethodField()

    def get_path(self, obj):
        instanceType = obj._meta.model.__name__
        classInstance = None
        locationInstance = None
        path = ""
        if instanceType == "Project":
            classInstance = getattr(obj, "projectClass", None)
            locationInstance = getattr(obj, "projectLocation", None)
        elif instanceType == "ProjectClass":
            classInstance = obj
        elif instanceType == "ProjectLocation":
            classInstance = obj.parentClass
            locationInstance = obj
        elif instanceType == "ProjectGroup":
            classInstance = getattr(obj, "classRelation", None)
            locationInstance = getattr(obj, "locationRelation", None)

        if classInstance is None:
            return path

        if classInstance.parent is not None and classInstance.parent.parent is not None:
            path = "{}/{}/{}".format(
                str(classInstance.parent.parent.id),
                str(classInstance.parent.id),
                str(classInstance.id),
            )
        elif classInstance.parent is not None:
            path = "{}/{}".format(
                str(classInstance.parent.id),
                str(classInstance.id),
            )
        else:
            path = str(classInstance.id)

        if "suurpiiri" in classInstance.name.lower():
            return path

        if locationInstance is None:
            return path

        if locationInstance.parent is None:
            path = path + "/{}".format(str(locationInstance.id))
        if (
            locationInstance.parent is not None
            and locationInstance.parent.parent is not None
        ):
            path = path + "/{}".format(str(locationInstance.parent.parent.id))
        if (
            locationInstance.parent is not None
            and locationInstance.parent.parent is None
        ):
            path = path + "/{}".format(str(locationInstance.parent.id))

        return path

    def get_phase(self, obj):
        if not hasattr(obj, "phase") or obj.phase is None:
            return None
        return ProjectPhaseSerializer(obj.phase).data

    def get_name(self, obj):
        return obj.name

    def get_id(self, obj):
        return obj.id

    def get_type(self, obj):
        instanceType = obj._meta.model.__name__
        if instanceType == "ProjectLocation":
            return "locations"
        elif instanceType == "ProjectClass":
            return "classes"
        elif instanceType == "Project":
            return "projects"
        elif instanceType == "ProjectGroup":
            return "groups"
        else:
            raise ValidationError(detail={"type": "Invalid value"}, code="invalid")

    def get_hashTags(self, obj):
        if not hasattr(obj, "hashTags") or obj.hashTags is None:
            return []

        include_hashtags_list = self.context.get("hashtags_include", [])
        projectHashtags = ProjectHashtagSerializer(obj.hashTags, many=True).data
        projectHashtags = list(
            filter(
                lambda hashtag: hashtag["id"] in include_hashtags_list,
                projectHashtags,
            )
        )
        return projectHashtags

    def get_programmed(self, obj):
        if hasattr(obj, "programmed"):
            return obj.programmed
        return None


class ProjectGroupSerializer(DynamicFieldsModelSerializer, FinancialSumSerializer):
    projects = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False, allow_empty=True
    )

    def validate_projects(self, projectIds):
        """
        Check that project doesn't already belong to a group
        """

        if projectIds is not None and len(projectIds) > 0:
            # Get existing group instance if there is any
            # In case of a PATCH or POST request to a group
            # None if POST request for a new group
            group = getattr(self, "instance", None)
            for projectId in projectIds:
                project = get_object_or_404(Project, pk=projectId)
                if (
                    (
                        # PATCH request to existing group
                        # Check if a project is in a group which is not same as the group being patched
                        # Means a project is being assigned to this group which belongs to another group already
                        group is not None
                        and project.projectGroup is not None
                        and project.projectGroup.id != group.id
                    )
                    or
                    # POST request for new group
                    # A project in the request already belongs to another group
                    (group is None and project.projectGroup is not None)
                ):
                    raise ValidationError(
                        detail="Project: {} cannot be assigned to this group. It already belongs to group: {} with groupId: {}".format(
                            project.name,
                            project.projectGroup.name,
                            project.projectGroup_id,
                        ),
                        code="project_in_group",
                    )
        return projectIds

    class Meta(BaseMeta):
        model = ProjectGroup
        validators = [
            UniqueTogetherValidator(
                queryset=ProjectGroup.objects.all(),
                fields=["name", "classRelation", "locationRelation"],
            ),
        ]

    @override
    def update(self, instance, validated_data):
        # new project Ids
        updatedProjectIds = validated_data.pop("projects", [])
        # get all project ids that currently belong to this group
        existingProjectIds = instance.project_set.all().values_list("id", flat=True)
        # project that are to be removed from this group
        removedProjects = list(set(existingProjectIds) - set(updatedProjectIds))
        if len(updatedProjectIds) > 0:
            for projectId in updatedProjectIds:
                if projectId not in existingProjectIds:
                    project = get_object_or_404(Project, pk=projectId)
                    project.projectGroup = instance
                    project.save()

        if len(removedProjects) > 0:
            for projectId in removedProjects:
                project = get_object_or_404(Project, pk=projectId)
                project.projectGroup = None
                project.save()

        return super(ProjectGroupSerializer, self).update(instance, validated_data)

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


class ProjectLocationSerializer(FinancialSumSerializer, serializers.ModelSerializer):
    class Meta(BaseMeta):
        model = ProjectLocation


class ProjectClassSerializer(FinancialSumSerializer, serializers.ModelSerializer):
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
        queryset, _ = ProjectFinancialService.get_or_create(
            project_id=project.id, year=year
        )

        return ProjectFinancialSerializer(queryset, many=False).data

    class Meta(BaseMeta):
        model = Project


class ProjectGetSerializer(DynamicFieldsModelSerializer, ProjectWithFinancesSerializer):
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
    locked = serializers.SerializerMethodField()
    finances = serializers.SerializerMethodField()
    spentBudget = serializers.SerializerMethodField(method_name="get_spent_budget")
    pwFolderLink = serializers.SerializerMethodField(method_name="get_pw_folder_link")
    projectWiseService = None

    class Meta(BaseMeta):
        model = Project

    def get_spent_budget(self, project: Project):
        year = self.context.get("finance_year", date.today().year)
        if year is None:
            year = date.today().year
        spentBudget = ProjectFinancialService.find_by_project_id_and_max_year(
            project_id=project.id, max_year=year
        ).aggregate(spent_budget=Sum("budgetProposalCurrentYearPlus0", default=0))[
            "spent_budget"
        ]

        return int(spentBudget)

    def get_pw_folder_link(self, project: Project):
        if not self.context.get("get_pw_link", False) or project.hkrId is None:
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

    def get_locked(self, project):
        try:
            lockData = ProjectLockSerializer(project.lock, many=False).data
            return lockData
        except:
            return None

    def get_projectReadiness(self, project):
        return project.projectReadiness()


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

    def get_projectReadiness(self, project):
        return project.projectReadiness()

    def validate_estPlanningStart(self, estPlanningStart):
        """
        Function to check if a project is locked and the dateField estPlanningStart in the Project PATCH
        request is not set to a date earlier than the locked field planningStartYear on the existing Project instance
        """
        project = getattr(self, "instance", None)
        if project is not None and hasattr(project, "lock"):
            planningStartYear = project.planningStartYear
            if planningStartYear is not None and estPlanningStart is not None:
                if estPlanningStart.year < planningStartYear:
                    raise ValidationError(
                        detail="estPlanningStart date cannot be set to a earlier date than Start year of planning when project is locked",
                        code="estPlanningStart_et_planningStartYear",
                    )

        return estPlanningStart

    def validate_estConstructionEnd(self, estConstructionEnd):
        """
        Function to check if a project is locked and the dateField estConstructionEnd in the Project PATCH
        request is not set to a date later than the locked field constructionEndYear on the existing Project instance
        """
        project = getattr(self, "instance", None)
        if project is not None and hasattr(project, "lock"):
            constructionEndYear = project.constructionEndYear
            if constructionEndYear is not None and estConstructionEnd is not None:
                if estConstructionEnd.year > constructionEndYear:
                    raise ValidationError(
                        detail="estConstructionEnd date cannot be set to a later date than End year of construction when project is locked",
                        code="estConstructionEnd_lt_constructionEndYear",
                    )

        return estConstructionEnd

    def _is_projectClass_projectLocation_valid(
        self,
        projectLocation,
        projectClass,
    ) -> bool:
        if projectClass is None or projectLocation is None:
            return True
        if projectClass.parent is None or projectClass.parent.parent is None:
            return True
        if (
            "suurpiiri" in projectClass.name.lower()
            and len(projectClass.name.split()) == 2
            and (
                projectLocation.path.startswith(projectClass.name.split()[0])
                or projectLocation.path.startswith(projectClass.name.split()[0][:-2])
            )
        ):
            return True
        elif "suurpiiri" not in projectClass.name.lower():
            return True
        else:
            return False

    def validate_projectClass(self, projectClass):
        """
        Function to validate if a Project belongs to a specific Class then it should belong to a related Location
        """
        project = getattr(self, "instance", None)
        if (
            "projectLocation" in self.get_initial()
            and self.get_initial().get("projectLocation") is None
        ):
            return projectClass

        projectLocation = (
            ProjectLocation.objects.get(id=self.get_initial().get("projectLocation"))
            if self.get_initial().get("projectLocation", None) is not None
            else None
        )

        if (
            projectLocation is None
            and project is not None
            and project.projectLocation is not None
        ):
            projectLocation = project.projectLocation

        if not self._is_projectClass_projectLocation_valid(
            projectLocation=projectLocation, projectClass=projectClass
        ):
            raise ValidationError(
                detail="subClass: {} with path: {} cannot have the location: {} under it.".format(
                    projectClass.name,
                    projectClass.path,
                    projectLocation.name,
                ),
                code="projectClass_invalid_projectLocation",
            )

        return projectClass

    def validate_projectLocation(self, projectLocation):
        """
        Function to validate if a Project belongs to a specific Location then it should belong to a related Class
        """
        project = getattr(self, "instance", None)
        projectClass = (
            ProjectClass.objects.get(id=self.get_initial().get("projectClass", None))
            if self.get_initial().get("projectClass", None) is not None
            else None
        )

        if (
            projectClass is None
            and project is not None
            and project.projectClass is not None
        ):
            projectClass = project.projectClass
        if not self._is_projectClass_projectLocation_valid(
            projectLocation=projectLocation, projectClass=projectClass
        ):
            raise ValidationError(
                "Location: {} with path: {} cannot be under the subClass: {}".format(
                    projectLocation.name,
                    projectLocation.path,
                    projectClass.name,
                ),
                code="projectLocation_invalid_projectClass",
            )
        return projectLocation

    @override
    def update(self, instance, validated_data):
        """
        Overriding the update method to populate ProjectLockStatus Table
        with appropriate lock status based on the phase and validating if
        locked fields are not being updated
        """

        # Check if project is locked and any locked fields are not being updated
        if hasattr(instance, "lock"):
            lockedFields = [
                "phase",
                "planningStartYear",
                "constructionEndYear",
                "programmed",
                "projectClass",
                "projectLocation",
                "siteId",
                "realizedCost",
                "budgetOverrunAmount",
                "budgetForecast1CurrentYear",
                "budgetForecast2CurrentYear",
                "budgetForecast3CurrentYear",
                "budgetForecast4CurrentYear",
            ]
            for field in lockedFields:
                if validated_data.get(field, None) is not None:
                    raise ValidationError(
                        "The field {} cannot be modified when the project is locked".format(
                            field
                        ),
                        code="project_locked",
                    )
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
