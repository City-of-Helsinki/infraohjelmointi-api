from datetime import datetime
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
from rest_framework.exceptions import ParseError, ValidationError
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


class searchResultSerializer(serializers.Serializer):
    name = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    hashTags = serializers.SerializerMethodField()
    phase = serializers.SerializerMethodField()
    path = serializers.SerializerMethodField()

    def get_path(self, obj):
        instanceType = obj._meta.model.__name__
        classInstance = None
        if instanceType == "Project":
            classInstance = getattr(obj, "projectClass", None)
        elif instanceType in ["ProjectLocation", "ProjectClass"]:
            classInstance = obj
        elif instanceType == "ProjectGroup":
            classInstance = getattr(obj, "classRelation", None)

        if classInstance is None:
            return ""

        if classInstance.parent is not None and classInstance.parent.parent is not None:
            return "{}/{}/{}".format(
                str(classInstance.parent.parent.id),
                str(classInstance.parent.id),
                str(classInstance.id),
            )
        elif classInstance.parent is not None:
            return "{}/{}".format(
                str(classInstance.parent.id),
                str(classInstance.id),
            )
        else:
            return str(classInstance.id)

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
                    raise ValidationError(
                        detail="Project: {} with id: {} already belongs to the group: {} with id: {}".format(
                            project.name,
                            projectId,
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
    locked = serializers.SerializerMethodField()

    class Meta(BaseMeta):
        model = Project

    def get_locked(self, obj):
        try:
            lockData = ProjectLockSerializer(obj.lock, many=False).data
            return lockData
        except:
            return None

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

    def _format_date(self, dateStr):
        for f in ["%Y-%m-%d", "%d.%m.%Y"]:
            try:
                return datetime.strptime(dateStr, f).date()
            except ValueError:
                pass
        raise ParseError(detail="Invalid format", code="invalid")

    def validate_estPlanningStart(self, estPlanningStart):
        """
        Function to check if a project is locked and the dateField estPlanningStart in the Project PATCH
        request is not set to a date earlier than the locked field planningStartYear on the existing Project instance
        """

        project = getattr(self, "instance", None)
        estPlanningEnd = self.get_initial().get("estPlanningEnd", None)
        planningStartYear = self.get_initial().get("planningStartYear", None)
        estConstructionStart = self.get_initial().get("estConstructionStart", None)
        estConstructionEnd = self.get_initial().get("estConstructionEnd", None)
        constructionEndYear = self.get_initial().get("constructionEndYear", None)

        if estPlanningEnd is not None:
            estPlanningEnd = self._format_date(estPlanningEnd)
        elif (
            estPlanningEnd is None
            and project is not None
            and project.estPlanningEnd is not None
        ):
            estPlanningEnd = project.estPlanningEnd
        if (
            planningStartYear is None
            and project is not None
            and project.planningStartYear is not None
        ):
            planningStartYear = project.planningStartYear

        if (
            constructionEndYear is None
            and project is not None
            and project.constructionEndYear is not None
        ):
            constructionEndYear = project.constructionEndYear

        if estConstructionStart is not None:
            estConstructionStart = self._format_date(estConstructionStart)
        elif (
            estConstructionStart is None
            and project is not None
            and project.estConstructionStart is not None
        ):
            estConstructionStart = project.estConstructionStart

        if estConstructionEnd is not None:
            estConstructionEnd = self._format_date(estConstructionEnd)
        elif (
            estConstructionEnd is None
            and project is not None
            and project.estConstructionEnd is not None
        ):
            estConstructionEnd = project.estConstructionEnd

        if planningStartYear is not None and estPlanningStart is not None:
            if estPlanningStart.year != int(planningStartYear):
                raise ValidationError(
                    detail="Year should be consistent with the field planningStartYear",
                    code="estPlanningStart_ne_planningStartYear",
                )
        if constructionEndYear is not None and estPlanningStart is not None:
            if estPlanningStart.year > int(constructionEndYear):
                raise ValidationError(
                    detail="Date cannot be later than constructionEndYear",
                    code="estPlanningStart_lt_constructionEndYear",
                )
        if estPlanningEnd is not None and estPlanningStart is not None:
            if estPlanningStart > estPlanningEnd:
                raise ValidationError(
                    detail="Date cannot be later than estPlanningEnd",
                    code="estPlanningStart_lt_estPlanningEnd",
                )
        if estConstructionStart is not None and estPlanningStart is not None:
            if estPlanningStart > estConstructionStart:
                raise ValidationError(
                    detail="Date cannot be later than estConstructionStart",
                    code="estPlanningStart_lt_estConstructionStart",
                )
        if estConstructionEnd is not None and estPlanningStart is not None:
            if estPlanningStart > estConstructionEnd:
                raise ValidationError(
                    detail="Date cannot be later than estConstructionEnd",
                    code="estPlanningStart_lt_estConstructionEnd",
                )

        return estPlanningStart

    def validate_estPlanningEnd(self, estPlanningEnd):
        """
        Function to check if a project is locked and the dateField estPlanningStart in the Project PATCH
        request is not set to a date earlier than the locked field planningStartYear on the existing Project instance
        """

        project = getattr(self, "instance", None)
        estPlanningStart = self.get_initial().get("estPlanningStart", None)
        planningStartYear = self.get_initial().get("planningStartYear", None)
        estConstructionStart = self.get_initial().get("estConstructionStart", None)
        estConstructionEnd = self.get_initial().get("estConstructionEnd", None)
        constructionEndYear = self.get_initial().get("constructionEndYear", None)

        if estPlanningStart is not None:
            estPlanningStart = self._format_date(estPlanningStart)
        elif (
            estPlanningStart is None
            and project is not None
            and project.estPlanningStart is not None
        ):
            estPlanningStart = project.estPlanningStart
        if (
            planningStartYear is None
            and project is not None
            and project.planningStartYear is not None
        ):
            planningStartYear = project.planningStartYear

        if (
            constructionEndYear is None
            and project is not None
            and project.constructionEndYear is not None
        ):
            constructionEndYear = project.constructionEndYear
        if estConstructionStart is not None:
            estConstructionStart = self._format_date(estConstructionStart)
        elif (
            estConstructionStart is None
            and project is not None
            and project.estConstructionStart is not None
        ):
            estConstructionStart = project.estConstructionStart
        if estConstructionEnd is not None:
            estConstructionEnd = self._format_date(estConstructionEnd)
        elif (
            estConstructionEnd is None
            and project is not None
            and project.estConstructionEnd is not None
        ):
            estConstructionEnd = project.estConstructionEnd

        if planningStartYear is not None and estPlanningEnd is not None:
            if estPlanningEnd.year < int(planningStartYear):
                raise ValidationError(
                    detail="Date cannot be earlier than planningStartYear",
                    code="estPlanningEnd_et_planningStartYear",
                )

        if constructionEndYear is not None and estPlanningEnd is not None:
            if estPlanningEnd.year > int(constructionEndYear):
                raise ValidationError(
                    detail="Date cannot be later than constructionEndYear",
                    code="estPlanningEnd_lt_constructionEndYear",
                )
        if estPlanningEnd is not None and estPlanningStart is not None:
            if estPlanningEnd < estPlanningStart:
                raise ValidationError(
                    detail="Date cannot be earlier than estPlanningStart",
                    code="estPlanningEnd_et_estPlanningStart",
                )
        if estConstructionStart is not None and estPlanningEnd is not None:
            if estPlanningEnd > estConstructionStart:
                raise ValidationError(
                    detail="Date cannot be later than estConstructionStart",
                    code="estPlanningEnd_lt_estConstructionStart",
                )
        if estConstructionEnd is not None and estPlanningEnd is not None:
            if estPlanningEnd > estConstructionEnd:
                raise ValidationError(
                    detail="Date cannot be later than estConstructionEnd",
                    code="estPlanningEnd_lt_estConstructionEnd",
                )

        return estPlanningEnd

    def validate_estConstructionStart(self, estConstructionStart):
        """
        Function to check if a project is locked and the dateField estPlanningStart in the Project PATCH
        request is not set to a date earlier than the locked field planningStartYear on the existing Project instance
        """

        project = getattr(self, "instance", None)
        estPlanningStart = self.get_initial().get("estPlanningStart", None)
        estPlanningEnd = self.get_initial().get("estPlanningEnd", None)
        planningStartYear = self.get_initial().get("planningStartYear", None)
        estConstructionEnd = self.get_initial().get("estConstructionEnd", None)
        constructionEndYear = self.get_initial().get("constructionEndYear", None)

        if estPlanningStart is not None:
            estPlanningStart = self._format_date(estPlanningStart)
        elif (
            estPlanningStart is None
            and project is not None
            and project.estPlanningStart is not None
        ):
            estPlanningStart = project.estPlanningStart

        if estPlanningEnd is not None:
            estPlanningEnd = self._format_date(estPlanningEnd)
        elif (
            estPlanningEnd is None
            and project is not None
            and project.estPlanningEnd is not None
        ):
            estPlanningEnd = project.estPlanningEnd
        if (
            planningStartYear is None
            and project is not None
            and project.planningStartYear is not None
        ):
            planningStartYear = project.planningStartYear

        if (
            constructionEndYear is None
            and project is not None
            and project.constructionEndYear is not None
        ):
            constructionEndYear = project.constructionEndYear

        if estConstructionEnd is not None:
            estConstructionEnd = self._format_date(estConstructionEnd)
        elif (
            estConstructionEnd is None
            and project is not None
            and project.estConstructionEnd is not None
        ):
            estConstructionEnd = project.estConstructionEnd

        if estConstructionStart is not None and estPlanningStart is not None:
            if estConstructionStart < estPlanningStart:
                raise ValidationError(
                    detail="Date cannot be earlier than estPlanningStart",
                    code="estConstructionStart_et_estPlanningStart",
                )
        if estConstructionStart is not None and estPlanningEnd is not None:
            if estConstructionStart < estPlanningEnd:
                raise ValidationError(
                    detail="Date cannot be earlier than estPlanningEnd",
                    code="estConstructionStart_et_estPlanningEnd",
                )
        if estConstructionStart is not None and planningStartYear is not None:
            if estConstructionStart.year < int(planningStartYear):
                raise ValidationError(
                    detail="Date cannot be earlier than planningStartYear",
                    code="estConstructionStart_et_planningStartYear",
                )

        if estConstructionStart is not None and constructionEndYear is not None:
            if estConstructionStart.year > int(constructionEndYear):
                raise ValidationError(
                    detail="Date cannot be later than constructionEndYear",
                    code="estConstructionStart_lt_constructionEndYear",
                )

        if estConstructionStart is not None and estConstructionEnd is not None:
            if estConstructionStart > estConstructionEnd:
                raise ValidationError(
                    detail="Date cannot be later than estConstructionEnd",
                    code="estConstructionStart_lt_estConstructionEnd",
                )

        return estConstructionStart

    def validate_estConstructionEnd(self, estConstructionEnd):
        """
        Function to check if a project is locked and the dateField estPlanningStart in the Project PATCH
        request is not set to a date earlier than the locked field planningStartYear on the existing Project instance
        """

        project = getattr(self, "instance", None)
        estPlanningStart = self.get_initial().get("estPlanningStart", None)
        estPlanningEnd = self.get_initial().get("estPlanningEnd", None)
        planningStartYear = self.get_initial().get("planningStartYear", None)
        estConstructionStart = self.get_initial().get("estConstructionStart", None)
        constructionEndYear = self.get_initial().get("constructionEndYear", None)

        if estPlanningStart is not None:
            estPlanningStart = self._format_date(estPlanningStart)
        elif (
            estPlanningStart is None
            and project is not None
            and project.estPlanningStart is not None
        ):
            estPlanningStart = project.estPlanningStart

        if estPlanningEnd is not None:
            estPlanningEnd = self._format_date(estPlanningEnd)
        elif (
            estPlanningEnd is None
            and project is not None
            and project.estPlanningEnd is not None
        ):
            estPlanningEnd = project.estPlanningEnd
        if (
            planningStartYear is None
            and project is not None
            and project.planningStartYear is not None
        ):
            planningStartYear = project.planningStartYear

        if (
            constructionEndYear is None
            and project is not None
            and project.constructionEndYear is not None
        ):
            constructionEndYear = project.constructionEndYear

        if estConstructionStart is not None:
            estConstructionStart = self._format_date(estConstructionStart)

        elif (
            estConstructionStart is None
            and project is not None
            and project.estConstructionStart is not None
        ):
            estConstructionStart = project.estConstructionStart

        if planningStartYear is not None and estConstructionEnd is not None:
            if estConstructionEnd.year < int(planningStartYear):
                raise ValidationError(
                    detail="Date cannot be earlier than planningStartYear",
                    code="estConstructionEnd_et_planningStartYear",
                )
        if constructionEndYear is not None and estConstructionEnd is not None:
            if estConstructionEnd.year != int(constructionEndYear):
                raise ValidationError(
                    detail="Year should be consistent with the field estConstructionEnd",
                    code="estConstructionEnd_et_constructionEndYear",
                )
        if estConstructionEnd is not None and estPlanningStart is not None:
            if estConstructionEnd < estPlanningStart:
                raise ValidationError(
                    detail="Date cannot be earlier than estPlanningStart",
                    code="estConstructionEnd_et_estPlanningStart",
                )
        if estConstructionEnd is not None and estPlanningEnd is not None:
            if estConstructionEnd < estPlanningEnd:
                raise ValidationError(
                    detail="Date cannot be earlier than estPlanningEnd",
                    code="estConstructionEnd_et_estPlanningEnd",
                )
        if estConstructionStart is not None and estConstructionEnd is not None:
            if estConstructionEnd < estConstructionStart:
                raise ValidationError(
                    detail="Date cannot be earlier than estConstructionStart",
                    code="estConstructionEnd_et_estConstructionStart",
                )

        return estConstructionEnd

    def validate_planningStartYear(self, planningStartYear):
        """
        Function to check if a project is locked and the dateField estPlanningStart in the Project PATCH
        request is not set to a date earlier than the locked field planningStartYear on the existing Project instance
        """

        project = getattr(self, "instance", None)
        estPlanningStart = self.get_initial().get("estPlanningStart", None)
        estPlanningEnd = self.get_initial().get("estPlanningEnd", None)
        estConstructionStart = self.get_initial().get("estConstructionStart", None)
        estConstructionEnd = self.get_initial().get("estConstructionEnd", None)
        constructionEndYear = self.get_initial().get("constructionEndYear", None)

        if (
            constructionEndYear is None
            and project is not None
            and project.constructionEndYear is not None
        ):
            constructionEndYear = project.constructionEndYear

        if estPlanningStart is not None:
            estPlanningStart = self._format_date(estPlanningStart)
        elif (
            estPlanningStart is None
            and project is not None
            and project.estPlanningStart is not None
        ):
            estPlanningStart = project.estPlanningStart

        if estPlanningEnd is not None:
            estPlanningEnd = self._format_date(estPlanningEnd)
        elif (
            estPlanningEnd is None
            and project is not None
            and project.estPlanningEnd is not None
        ):
            estPlanningEnd = project.estPlanningEnd

        if estConstructionStart is not None:
            estConstructionStart = self._format_date(estConstructionStart)
        elif (
            estConstructionStart is None
            and project is not None
            and project.estConstructionStart is not None
        ):
            estConstructionStart = project.estConstructionStart

        if estConstructionEnd is not None:
            estConstructionEnd = self._format_date(estConstructionEnd)
        elif (
            estConstructionEnd is None
            and project is not None
            and project.estConstructionEnd is not None
        ):
            estConstructionEnd = project.estConstructionEnd

        if planningStartYear is not None and estPlanningStart is not None:
            if planningStartYear != estPlanningStart.year:
                raise ValidationError(
                    detail="Year should be consistent with the field estPlanningStart",
                    code="planningStartYear_ne_estPlanningStart",
                )
        if planningStartYear is not None and estPlanningEnd is not None:
            if planningStartYear > estPlanningEnd.year:
                raise ValidationError(
                    detail="Year cannot be later than estPlanningEnd",
                    code="planningStartYear_lt_estPlanningEnd",
                )
        if estConstructionStart is not None and planningStartYear is not None:
            if planningStartYear > estConstructionStart.year:
                raise ValidationError(
                    detail="Year cannot be later than estConstructionStart",
                    code="planningStartYear_lt_estConstructionStart",
                )

        if estConstructionEnd is not None and planningStartYear is not None:
            if planningStartYear > estConstructionEnd.year:
                raise ValidationError(
                    detail="Year cannot be later than estConstructionEnd",
                    code="planningStartYear_lt_estConstructionEnd",
                )

        if constructionEndYear is not None and planningStartYear is not None:
            if planningStartYear > int(constructionEndYear):
                raise ValidationError(
                    detail="Year cannot be later than constructionEndYear",
                    code="planningStartYear_lt_constructionEndYear",
                )

        return planningStartYear

    def validate_constructionEndYear(self, constructionEndYear):
        """
        Function to check if a project is locked and the dateField estPlanningStart in the Project PATCH
        request is not set to a date earlier than the locked field constructionEndYear on the existing Project instance
        """

        project = getattr(self, "instance", None)
        planningStartYear = self.get_initial().get("planningStartYear", None)
        estPlanningStart = self.get_initial().get("estPlanningStart", None)
        estPlanningEnd = self.get_initial().get("estPlanningEnd", None)
        estConstructionStart = self.get_initial().get("estConstructionStart", None)
        estConstructionEnd = self.get_initial().get("estConstructionEnd", None)
        if (
            planningStartYear is None
            and project is not None
            and project.planningStartYear is not None
        ):
            planningStartYear = project.planningStartYear
        if estPlanningStart is not None:
            estPlanningStart = self._format_date(estPlanningStart)
        elif (
            estPlanningStart is None
            and project is not None
            and project.estPlanningStart is not None
        ):
            estPlanningStart = project.estPlanningStart

        if estPlanningEnd is not None:
            estPlanningEnd = self._format_date(estPlanningEnd)
        elif (
            estPlanningEnd is None
            and project is not None
            and project.estPlanningEnd is not None
        ):
            estPlanningEnd = project.estPlanningEnd

        if estConstructionStart is not None:
            estConstructionStart = self._format_date(estConstructionStart)
        elif (
            estConstructionStart is None
            and project is not None
            and project.estConstructionStart is not None
        ):
            estConstructionStart = project.estConstructionStart

        if estConstructionEnd is not None:
            estConstructionEnd = self._format_date(estConstructionEnd)
        elif (
            estConstructionEnd is None
            and project is not None
            and project.estConstructionEnd is not None
        ):
            estConstructionEnd = project.estConstructionEnd

        if constructionEndYear is not None and estPlanningStart is not None:
            if constructionEndYear < estPlanningStart.year:
                raise ValidationError(
                    detail="Year cannot be earlier than estPlanningStart",
                    code="constructionEndYear_et_estPlanningStart",
                )
        if constructionEndYear is not None and planningStartYear is not None:
            if constructionEndYear < int(planningStartYear):
                raise ValidationError(
                    detail="Year cannot be earlier than planningStartYear",
                    code="constructionEndYear_et_planningStartYear",
                )
        if constructionEndYear is not None and estPlanningEnd is not None:
            if constructionEndYear < estPlanningEnd.year:
                raise ValidationError(
                    detail="Year cannot be earlier than estPlanningEnd",
                    code="constructionEndYear_et_estPlanningEnd",
                )
        if estConstructionStart is not None and constructionEndYear is not None:
            if constructionEndYear < estConstructionStart.year:
                raise ValidationError(
                    detail="Year cannot be earlier than estConstructionStart",
                    code="constructionEndYear_et_estConstructionStart",
                )

        if estConstructionEnd is not None and constructionEndYear is not None:
            if constructionEndYear != estConstructionEnd.year:
                raise ValidationError(
                    detail="Year should be consistent with the field estConstructionEnd",
                    code="constructionEndYear_ne_estConstructionEnd",
                )

        return constructionEndYear

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
        projectLocation = (
            ProjectLocation.objects.get(
                id=self.get_initial().get("projectLocation", None)
            )
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

    # Commented out automatic locking logic when project is created with phase construction
    # @override
    # def create(self, validated_data):
    #     """
    #     Overriding the create method to populate ProjectLockStatus Table
    #     with appropriate lock status based on the phase
    #     """
    #     newPhase = validated_data.get("phase", None)
    #     project = super(ProjectCreateSerializer, self).create(validated_data)
    #     if newPhase is not None and newPhase.value == "construction":
    #         project.lock.create(lockType="status_construction", lockedBy=None)

    #     return project

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
                    raise ValidationError(
                        "The field {} cannot be modified when the project is locked".format(
                            field
                        ),
                        code="project_locked",
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
