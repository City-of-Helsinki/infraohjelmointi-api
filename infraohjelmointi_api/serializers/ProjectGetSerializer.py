from datetime import date
import datetime
from os import path
from infraohjelmointi_api.models import Project
from infraohjelmointi_api.serializers import (
    BaseMeta,
    DynamicFieldsModelSerializer,
    PersonSerializer,
    ProjectLockSerializer,
)
from infraohjelmointi_api.services.ProjectWiseService import (
    PWProjectNotFoundError,
    PWProjectResponseError,
)
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
from infraohjelmointi_api.serializers.ProjectWithFinancesSerializer import (
    ProjectWithFinancesSerializer,
)
from infraohjelmointi_api.serializers.SapCurrentYearSerializer import SapCurrentYearSerializer
from infraohjelmointi_api.services.ProjectWiseService import ProjectWiseService
from infraohjelmointi_api.services.SapCurrentYearService import SapCurrentYearService
from rest_framework import serializers
import environ
from overrides import override

env = environ.Env()
env.escape_proxy = True

if path.exists(".env"):
    env.read_env(".env")


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
    frameEstPlanningStart = serializers.DateField(format="%d.%m.%Y")
    frameEstPlanningEnd = serializers.DateField(format="%d.%m.%Y")
    category = ProjectCategorySerializer(read_only=True)
    constructionPhaseDetail = ConstructionPhaseDetailSerializer(read_only=True)
    riskAssessment = ProjectRiskSerializer(read_only=True)
    estConstructionStart = serializers.DateField(format="%d.%m.%Y")
    estConstructionEnd = serializers.DateField(format="%d.%m.%Y")
    frameEstConstructionStart = serializers.DateField(format="%d.%m.%Y")
    frameEstConstructionEnd = serializers.DateField(format="%d.%m.%Y")
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
    currentYearsSapValues = serializers.SerializerMethodField(method_name="get_currentYearsSapValue")

    class Meta(BaseMeta):
        model = Project

    def get_spent_budget(self, project: Project):
        # this data should come from SAP, but since we don't have the connection yet
        # we'll just return zero for now
        """ year = self.context.get("finance_year", date.today().year)
        if year is None:
            year = date.today().year
        spentBudget = ProjectFinancialService.find_by_project_id_and_max_year(
            project_id=project.id, max_year=year
        ).aggregate(spent_budget=Sum("value", default=0))["spent_budget"]

        return int(spentBudget) """
        return 0

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

    def get_currentYearsSapValue(self):
        #Get the current year sap-costs for project card
        current_year = datetime.datetime.now().year

        sap_values = SapCurrentYearService.get_by_year(int(current_year))
        sap_serializer = SapCurrentYearSerializer(sap_values, many=True)
        sap_data = sap_serializer.data
        
        return sap_data

    @override
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # use context to check if coordinator class/locations are needed
        for_coordinator = self.context.get("for_coordinator", False)
        if for_coordinator == True:
            # if class is suurpiiri then goto its parent and check for coordinationClass since suurpiiri classes have no
            # coordination class
            rep["projectClass"] = (
                instance.projectClass.coordinatorClass.id
                if hasattr(instance.projectClass, "coordinatorClass")
                else instance.projectClass.parent.coordinatorClass.id
                if (
                    instance.projectClass != None
                    and "suurpiiri" in instance.projectClass.name.lower()
                    and hasattr(instance.projectClass.parent, "coordinatorClass")
                )
                else None
            )
            # if project location is division/subdivision then goto its district and get related coordination location else none
            rep["projectLocation"] = (
                instance.projectLocation.coordinatorLocation.id
                if (hasattr(instance.projectLocation, "coordinatorLocation"))
                else instance.projectLocation.parent.coordinatorLocation.id
                if (
                    instance.projectLocation != None
                    and instance.projectLocation.parent != None
                    and instance.projectLocation.parent.parent == None
                    and hasattr(instance.projectLocation.parent, "coordinatorLocation")
                )
                else instance.projectLocation.parent.parent.coordinatorLocation.id
                if (
                    instance.projectLocation != None
                    and instance.projectLocation.parent != None
                    and instance.projectLocation.parent.parent != None
                    and hasattr(
                        instance.projectLocation.parent.parent, "coordinatorLocation"
                    )
                )
                else None
            )
        return rep
