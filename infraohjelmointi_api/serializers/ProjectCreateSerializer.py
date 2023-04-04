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
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, ParseError
from datetime import datetime
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

    def _format_date(self, dateStr):
        for f in ["%Y-%m-%d", "%d.%m.%Y"]:
            try:
                return datetime.strptime(dateStr, f).date()
            except ValueError:
                pass
        raise ParseError(detail="Invalid format", code="invalid")

    def validate_estPlanningStart(self, estPlanningStart):
        if estPlanningStart is None:
            return estPlanningStart
        project = getattr(self, "instance", None)
        estPlanningEnd = self.get_initial().get("estPlanningEnd", None)

        if project is not None and hasattr(project, "lock"):
            planningStartYear = project.planningStartYear
            if planningStartYear is not None and estPlanningStart is not None:
                if estPlanningStart.year < planningStartYear:
                    raise ValidationError(
                        detail="estPlanningStart date cannot be set to a earlier date than Start year of planning when project is locked",
                        code="estPlanningStart_et_planningStartYear_locked",
                    )
        if estPlanningEnd is not None:
            estPlanningEnd = self._format_date(estPlanningEnd)
        elif (
            estPlanningEnd is None
            and project is not None
            and project.estPlanningEnd is not None
        ):
            estPlanningEnd = project.estPlanningEnd

        if estPlanningEnd is not None and estPlanningStart is not None:
            if estPlanningStart > estPlanningEnd:
                raise ValidationError(
                    detail="Date cannot be later than estPlanningEnd",
                    code="estPlanningStart_lt_estPlanningEnd",
                )

        return estPlanningStart

    def validate_estPlanningEnd(self, estPlanningEnd):
        project = getattr(self, "instance", None)
        estPlanningStart = self.get_initial().get("estPlanningStart", None)

        if estPlanningStart is not None:
            estPlanningStart = self._format_date(estPlanningStart)
        elif (
            estPlanningStart is None
            and project is not None
            and project.estPlanningStart is not None
        ):
            estPlanningStart = project.estPlanningStart

        if estPlanningEnd is not None and estPlanningStart is not None:
            if estPlanningEnd < estPlanningStart:
                raise ValidationError(
                    detail="Date cannot be earlier than estPlanningStart",
                    code="estPlanningEnd_et_estPlanningStart",
                )

        return estPlanningEnd

    def validate_presenceStart(self, presenceStart):
        project = getattr(self, "instance", None)
        presenceEnd = self.get_initial().get("presenceEnd", None)

        if presenceEnd is not None:
            presenceEnd = self._format_date(presenceEnd)
        elif (
            presenceEnd is None
            and project is not None
            and project.presenceEnd is not None
        ):
            presenceEnd = project.presenceEnd

        if presenceStart is not None and presenceEnd is not None:
            if presenceStart > presenceEnd:
                raise ValidationError(
                    detail="Date cannot be later than presenceEnd",
                    code="presenceStart_lt_presenceEnd",
                )

        return presenceStart

    def validate_presenceEnd(self, presenceEnd):
        project = getattr(self, "instance", None)
        presenceStart = self.get_initial().get("presenceStart", None)

        if presenceStart is not None:
            presenceStart = self._format_date(presenceStart)
        elif (
            presenceStart is None
            and project is not None
            and project.presenceStart is not None
        ):
            presenceStart = project.presenceStart

        if presenceEnd is not None and presenceStart is not None:
            if presenceEnd < presenceStart:
                raise ValidationError(
                    detail="Date cannot be earlier than presenceStart",
                    code="presenceEnd_et_presenceStart",
                )

        return presenceEnd

    def validate_visibilityStart(self, visibilityStart):
        project = getattr(self, "instance", None)
        visibilityEnd = self.get_initial().get("visibilityEnd", None)

        if visibilityEnd is not None:
            visibilityEnd = self._format_date(visibilityEnd)
        elif (
            visibilityEnd is None
            and project is not None
            and project.visibilityEnd is not None
        ):
            visibilityEnd = project.visibilityEnd

        if visibilityStart is not None and visibilityEnd is not None:
            if visibilityStart > visibilityEnd:
                raise ValidationError(
                    detail="Date cannot be later than visibilityEnd",
                    code="visibilityStart_lt_visibilityEnd",
                )

        return visibilityStart

    def validate_visibilityEnd(self, visibilityEnd):
        project = getattr(self, "instance", None)
        visibilityStart = self.get_initial().get("visibilityStart", None)

        if visibilityStart is not None:
            visibilityStart = self._format_date(visibilityStart)
        elif (
            visibilityStart is None
            and project is not None
            and project.visibilityStart is not None
        ):
            visibilityStart = project.visibilityStart

        if visibilityEnd is not None and visibilityStart is not None:
            if visibilityEnd < visibilityStart:
                raise ValidationError(
                    detail="Date cannot be earlier than visibilityStart",
                    code="visibilityEnd_et_visibilityStart",
                )

        return visibilityEnd

    def validate_estConstructionStart(self, estConstructionStart):
        if estConstructionStart is None:
            return estConstructionStart
        project = getattr(self, "instance", None)
        estConstructionEnd = self.get_initial().get("estConstructionEnd", None)

        if estConstructionEnd is not None:
            estConstructionEnd = self._format_date(estConstructionEnd)
        elif (
            estConstructionEnd is None
            and project is not None
            and project.estConstructionEnd is not None
        ):
            estConstructionEnd = project.estConstructionEnd

        if estConstructionEnd is not None and estConstructionStart is not None:
            if estConstructionStart > estConstructionEnd:
                raise ValidationError(
                    detail="Date cannot be later than estConstructionEnd",
                    code="estConstructionStart_lt_estConstructionEnd",
                )

        return estConstructionStart

    def validate_estConstructionEnd(self, estConstructionEnd):
        project = getattr(self, "instance", None)
        estConstructionStart = self.get_initial().get("estConstructionStart", None)
        if project is not None and hasattr(project, "lock"):
            constructionEndYear = project.constructionEndYear
            if constructionEndYear is not None and estConstructionEnd is not None:
                if estConstructionEnd.year > constructionEndYear:
                    raise ValidationError(
                        detail="estConstructionEnd date cannot be set to a later date than End year of construction when project is locked",
                        code="estConstructionEnd_lt_constructionEndYear_locked",
                    )

        if estConstructionStart is not None:
            estConstructionStart = self._format_date(estConstructionStart)
        elif (
            estConstructionStart is None
            and project is not None
            and project.estConstructionStart is not None
        ):
            estConstructionStart = project.estConstructionStart

        if estConstructionStart is not None and estConstructionEnd is not None:
            if estConstructionEnd < estConstructionStart:
                raise ValidationError(
                    detail="Date cannot be earlier than estConstructionStart",
                    code="estConstructionEnd_et_estConstructionStart",
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

    def validate_phase(self, phase):
        """
        Function to validate the field `phase`
        """
        if phase is None:
            return phase
        project = getattr(self, "instance", None)
        if phase.value == "programming":
            category = self.get_initial().get("category", None)
            planningStartYear = self.get_initial().get("planningStartYear", None)
            constructionEndYear = self.get_initial().get("constructionEndYear", None)

            if planningStartYear is None and project is not None:
                planningStartYear = project.planningStartYear

            if category is None and project is not None:
                category = project.category

            if constructionEndYear is None and project is not None:
                constructionEndYear = project.constructionEndYear

            if planningStartYear is None or constructionEndYear is None:
                raise ValidationError(
                    "planningStartYear and constructionEndYear must be populated if phase is `programming`",
                    code="programming_phase_missing_dates",
                )
            if category is None:
                raise ValidationError(
                    "category must be populated if phase is `programming`",
                    code="programming_phase_missing_category",
                )

        if phase.value == "draftInitiation":
            estPlanningStart = self.get_initial().get("estPlanningStart", None)
            estPlanningEnd = self.get_initial().get("estPlanningEnd", None)
            personPlanning = self.get_initial().get("personPlanning", None)

            if estPlanningStart is None and project is not None:
                estPlanningStart = project.estPlanningStart
            if estPlanningEnd is None and project is not None:
                estPlanningEnd = project.estPlanningEnd
            if personPlanning is None and project is not None:
                personPlanning = project.personPlanning

            if estPlanningStart is None or estPlanningEnd is None:
                raise ValidationError(
                    "estPlanningStart and estPlanningEnd must be populated if phase is `draftInitiation`",
                    code="draftInitiation_phase_missing_dates",
                )
            if personPlanning is None:
                raise ValidationError(
                    "personPlanning must be populated if phase is `draftInitiation`",
                    code="draftInitiation_phase_missing_personPlanning",
                )

        if phase.value == "construction":
            estConstructionStart = self.get_initial().get("estConstructionStart", None)
            estConstructionEnd = self.get_initial().get("estConstructionEnd", None)
            personConstruction = self.get_initial().get("personConstruction", None)

            if estConstructionStart is None and project is not None:
                estConstructionStart = project.estConstructionStart
            if estConstructionEnd is None and project is not None:
                estConstructionEnd = project.estConstructionEnd
            if personConstruction is None and project is not None:
                personConstruction = project.personConstruction

            if estConstructionStart is None or estConstructionEnd is None:
                raise ValidationError(
                    "estConstructionStart and estConstructionEnd must be populated if phase is `construction`",
                    code="construction_phase_missing_dates",
                )
            if personConstruction is None:
                raise ValidationError(
                    "personConstruction must be populated if phase is `construction`",
                    code="construction_phase_missing_personConstruction",
                )
        if phase.value == "warrantyPeriod":
            estConstructionEnd = self.get_initial().get("estConstructionEnd", None)

            if estConstructionEnd is not None:
                estConstructionEnd = self._format_date(estConstructionEnd)
            elif (
                estConstructionEnd is None
                and project is not None
                and project.estConstructionEnd is not None
            ):
                estConstructionEnd = project.estConstructionEnd

            if estConstructionEnd is not None:
                if datetime.today().date() < estConstructionEnd:
                    raise ValidationError(
                        "phase cannot be `warrantyPeriod` if current date is earlier than estConstructionEnd",
                        code="warrantyPeriod_phase_inconsistent_date",
                    )

        return phase

    def validate_constructionPhaseDetail(self, constructionPhaseDetail):
        if constructionPhaseDetail is None:
            return constructionPhaseDetail
        project = getattr(self, "instance", None)
        phase = self.get_initial().get("phase", None)
        if phase is not None:
            try:
                phase = ProjectPhase.objects.get(id=phase)
            except ProjectPhase.DoesNotExist:
                phase = None
        if phase is None and project is not None:
            phase = project.phase

        if phase is None or phase.value != "construction":
            raise ValidationError(
                "constructionPhase detail cannot be populated if phase is not `construction`",
                code="constructionPhaseDetail_invalid_phase",
            )

        return constructionPhaseDetail

    def validate_planningStartYear(self, planningStartYear):
        if planningStartYear is None:
            return planningStartYear
        project = getattr(self, "instance", None)
        constructionEndYear = self.get_initial().get("constructionEndYear", None)

        if (
            constructionEndYear is None
            and project is not None
            and project.constructionEndYear is not None
        ):
            constructionEndYear = project.constructionEndYear

        if constructionEndYear is not None and planningStartYear is not None:
            if planningStartYear > int(constructionEndYear):
                raise ValidationError(
                    detail="Year cannot be later than constructionEndYear",
                    code="planningStartYear_lt_constructionEndYear",
                )

        return planningStartYear

    def validate_constructionEndYear(self, constructionEndYear):
        if constructionEndYear is None:
            return constructionEndYear

        project = getattr(self, "instance", None)
        planningStartYear = self.get_initial().get("planningStartYear", None)

        if (
            planningStartYear is None
            and project is not None
            and project.planningStartYear is not None
        ):
            planningStartYear = project.planningStartYear

        if constructionEndYear is not None and planningStartYear is not None:
            if constructionEndYear < int(planningStartYear):
                raise ValidationError(
                    detail="Year cannot be earlier than planningStartYear",
                    code="constructionEndYear_et_planningStartYear",
                )

        return constructionEndYear

    def validate_programmed(self, programmed):
        if programmed is None:
            return programmed
        project = getattr(self, "instance", None)
        category = self.get_initial().get("category", None)
        phase = self.get_initial().get("phase", None)
        if phase is not None:
            try:
                phase = ProjectPhase.objects.get(id=phase)
            except ProjectPhase.DoesNotExist:
                phase = None
        if phase is None and project is not None:
            phase = project.phase
        if category is None and project is not None:
            category = project.category

        if category is None and programmed == True:
            raise ValidationError(
                detail="category must be populated if programmed is `True`",
                code="programmed_true_missing_category",
            )
        if programmed == False and (phase is None or phase.value != "proposal"):
            raise ValidationError(
                detail="phase must be set to `proposal` if programmed is `False`",
                code="programmed_false_missing_phase",
            )
        if programmed == True and (phase is None or phase.value != "programming"):
            raise ValidationError(
                detail="phase must be set to `programming` if programmed is `True`",
                code="programmed_true_missing_phase",
            )

        return programmed

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
