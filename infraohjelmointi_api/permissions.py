from infraohjelmointi_api.models.Project import Project
from infraohjelmointi_api.models.ProjectClass import ProjectClass
from infraohjelmointi_api.models.ProjectGroup import ProjectGroup
from rest_framework import permissions

GET = "GET"
POST = "POST"
PATCH = "PATCH"
DELETE = "DELETE"
PUT = "PUT"
SAFE_METHODS = [GET, POST, PATCH, DELETE, PUT]
DJANGO_BASE_READ_ONLY_ACTIONS = ["list", "retrieve"]
DJANGO_BASE_UPDATE_ONLY_ACTIONS = [
    "update",
    "partial_update",
]
DJANGO_BASE_CREATE_ONLY_ACTIONS = ["create"]
DJANGO_BASE_DELETE_ONLY_ACTIONS = ["destroy"]

#### Project Class Custom Actions ####
PROJECT_CLASS_COORDINATOR_GET_ACTIONS = ["get_coordinator_classes"]
PROJECT_CLASS_PLANNING_GET_ACTIONS = []
PROJECT_CLASS_ALL_GET_ACTIONS = [
    *PROJECT_CLASS_COORDINATOR_GET_ACTIONS,
    *PROJECT_CLASS_PLANNING_GET_ACTIONS,
]
PROJECT_CLASS_COORDINATOR_PATCH_ACTIONS = [
    "patch_coordinator_class_finances",
]
PROJECT_CLASS_PLANNING_PATCH_ACTIONS = []
PROJECT_CLASS_ALL_PATCH_ACTIONS = [
    *PROJECT_CLASS_COORDINATOR_PATCH_ACTIONS,
    *PROJECT_CLASS_PLANNING_PATCH_ACTIONS,
]
PROJECT_CLASS_ALL_ACTIONS = [
    *PROJECT_CLASS_ALL_GET_ACTIONS,
    *PROJECT_CLASS_ALL_PATCH_ACTIONS,
]

#### Project Location Custom Actions ####
PROJECT_LOCATION_COORDINATOR_GET_ACTIONS = ["get_coordinator_locations"]
PROJECT_LOCATION_PLANNING_GET_ACTIONS = []
PROJECT_LOCATION_ALL_GET_ACTIONS = [
    *PROJECT_LOCATION_COORDINATOR_GET_ACTIONS,
    *PROJECT_LOCATION_PLANNING_GET_ACTIONS,
]

PROJECT_LOCATION_COORDINATOR_PATCH_ACTIONS = ["patch_coordinator_location_finances"]
PROJECT_LOCATION_PLANNING_PATCH_ACTIONS = []
PROJECT_LOCATION_ALL_PATCH_ACTIONS = [
    *PROJECT_LOCATION_COORDINATOR_PATCH_ACTIONS,
    *PROJECT_LOCATION_PLANNING_PATCH_ACTIONS,
]
PROJECT_LOCATION_ALL_ACTIONS = [
    *PROJECT_LOCATION_ALL_GET_ACTIONS,
    *PROJECT_LOCATION_ALL_PATCH_ACTIONS,
]

#### Project Notes custom actions ####
PROJECT_NOTE_COORDINATOR_GET_ACTIONS = ["get_note_history", "get_note_history_by_user", "get_project_notes",]
PROJECT_NOTE_PLANNING_GET_ACTIONS = ["get_note_history", "get_note_history_by_user", "get_project_notes",]
PROJECT_NOTE_BASIC_ACTIONS = ["list", "retrieve", "create"]
PROJECT_NOTE_ALL_GET_ACTIONS = [
    *PROJECT_NOTE_PLANNING_GET_ACTIONS,
    *PROJECT_NOTE_COORDINATOR_GET_ACTIONS,
    *PROJECT_NOTE_BASIC_ACTIONS,
]
PROJECT_NOTE_ALL_ACTIONS = [*PROJECT_NOTE_ALL_GET_ACTIONS]

#### PROJECT Finances custom actions ####
PROJECT_FINANCES_PLANNING_GET_ACTIONS = ["get_project_finances_by_year"]
PROJECT_FINANCES_COORDINATOR_GET_ACTIONS = []
PROJECT_FINANCES_ALL_GET_ACTIONS = [
    *PROJECT_FINANCES_PLANNING_GET_ACTIONS,
    *PROJECT_FINANCES_COORDINATOR_GET_ACTIONS,
]
PROJECT_FINANCES_ALL_ACTIONS = [*PROJECT_FINANCES_ALL_GET_ACTIONS]

#### Project Custom Actions ####
PROJECT_COORDINATOR_GET_ACTIONS = [
    "get_coordinator_projects",
    "list_for_coordinator",
    "get_projects_for_coordinator",
]
PROJECT_PLANNING_GET_ACTIONS = [
    "get_projects_by_financial_year",
    "get_project_by_financial_year",
    "get_search_results",
    
]
PROJECT_ALL_GET_ACTIONS = [
    *PROJECT_COORDINATOR_GET_ACTIONS,
    *PROJECT_PLANNING_GET_ACTIONS,
]
PROJECT_COORDINATOR_PATCH_ACTIONS = []
PROJECT_PLANNING_PATCH_ACTIONS = [
    "patch_bulk_projects",
]
PROJECT_ALL_PATCH_ACTIONS = [
    *PROJECT_COORDINATOR_PATCH_ACTIONS,
    *PROJECT_PLANNING_PATCH_ACTIONS,
]
PROJECT_ALL_ACTIONS = [*PROJECT_ALL_GET_ACTIONS, *PROJECT_ALL_PATCH_ACTIONS]

#### SAP COST CUSTOM ACTIONS ####
SAP_COST_PLANNING_GET_ACTIONS = ["get_sap_cost_by_year"] 
SAP_COST_COORDINATOR_GET_ACTIONS = []
SAP_COST_ALL_GET_ACTIONS = [
    *SAP_COST_PLANNING_GET_ACTIONS,
    *SAP_COST_COORDINATOR_GET_ACTIONS,
]
SAP_COST_ALL_ACTIONS = [*SAP_COST_ALL_GET_ACTIONS]

#### Project group custom actions ####
PROJECT_GROUP_COORDINATOR_GET_ACTIONS = ["get_groups_for_coordinator"]
PROJECT_GROUP_PLANNING_GET_ACTIONS = []
PROJECT_GROUP_ALL_GET_ACTIONS = [
    *PROJECT_GROUP_COORDINATOR_GET_ACTIONS,
    *PROJECT_GROUP_PLANNING_GET_ACTIONS,
]
PROJECT_GROUP_ALL_ACTIONS = [*PROJECT_GROUP_ALL_GET_ACTIONS]

# ALL THE PERMISSION LOGIC GOES HERE, CAN BE REFACTORED LATER.
# THESE CLASSES CAN BE ADDED TO BaseViewSet.py To APPLY THE REQUIRED PERMISSIONS AND ROLES
# WORK STILL NEEDED

class IsViewer(permissions.BasePermission):
    def user_in_viewer_group(self, request):
        if "sl_dyn_kymp_sso_io_katselijat" in request.user.ad_groups.all().values_list(
            "name", flat=True
        ):
            return True

    def has_permission(self, request, view):
        if (
            request.user.is_authenticated
            and self.user_in_viewer_group(request=request)
            and request.method == GET
            and view.action
            in [
                *DJANGO_BASE_READ_ONLY_ACTIONS,
                *PROJECT_PLANNING_GET_ACTIONS,
                *PROJECT_CLASS_PLANNING_GET_ACTIONS,
                *PROJECT_LOCATION_PLANNING_GET_ACTIONS,
                *PROJECT_FINANCES_PLANNING_GET_ACTIONS,
                *PROJECT_GROUP_PLANNING_GET_ACTIONS,
                *SAP_COST_PLANNING_GET_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Viewer cannot edit anything or get an object instance
        return False

class IsCoordinator(permissions.BasePermission):
    def user_coordinator_group(self, request):
        if "sg_kymp_sso_io_koordinaattorit" in request.user.ad_groups.all().values_list(
            "name", flat=True
        ):
            return True
        
    def has_permission(self, request, view):
        if (
            request.user.is_authenticated
            and self.user_coordinator_group(request=request)
            and request.method in SAFE_METHODS
            and view.action in [
                *DJANGO_BASE_READ_ONLY_ACTIONS,
                *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
                *DJANGO_BASE_CREATE_ONLY_ACTIONS,
                *DJANGO_BASE_DELETE_ONLY_ACTIONS,
                *PROJECT_CLASS_ALL_ACTIONS,
                *PROJECT_LOCATION_ALL_ACTIONS,
                *PROJECT_GROUP_ALL_ACTIONS,
                *PROJECT_FINANCES_ALL_ACTIONS,
                *PROJECT_ALL_ACTIONS,
                *SAP_COST_ALL_ACTIONS,
                *PROJECT_NOTE_ALL_ACTIONS,
                ]
        ):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # Coordinators can edit and perform all operations so return true for all model instance actions
        return True

class IsPlanner(permissions.BasePermission):
    def user_in_planner_group(self, request):
        if "sg_kymp_sso_io_ohjelmoijat" in request.user.ad_groups.all().values_list(
            "name", flat=True
        ):
            return True
        
    def has_permission(self, request, view):
        if (
            request.user.is_authenticated
            and self.user_in_planner_group(request=request)
            and request.method in SAFE_METHODS
            and view.action in [
                *DJANGO_BASE_READ_ONLY_ACTIONS,
                *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
                *DJANGO_BASE_CREATE_ONLY_ACTIONS,
                *DJANGO_BASE_DELETE_ONLY_ACTIONS,
                *PROJECT_CLASS_ALL_ACTIONS,
                *PROJECT_LOCATION_ALL_ACTIONS,
                *PROJECT_GROUP_ALL_ACTIONS,
                *PROJECT_FINANCES_ALL_ACTIONS,
                *PROJECT_ALL_ACTIONS,
                *SAP_COST_ALL_ACTIONS,
                *PROJECT_NOTE_ALL_ACTIONS,
                ]
        ):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # Planners can edit and perform all operations so return true for all model instance actions
        return True

class IsProjectManager(permissions.BasePermission):
    def user_in_project_manager_group(self, request):
        if (
            "sg_kymp_sso_io_projektipaallikot"
            in request.user.ad_groups.all().values_list("name", flat=True)
        ):
            return True

    def has_permission(self, request, view):
        # has edit permissions for projects and notes
        # and read permissions
        if (
            request.user.is_authenticated
            and self.user_in_project_manager_group(request=request)
            and request.method in SAFE_METHODS
            and view.action
            in [
                *DJANGO_BASE_READ_ONLY_ACTIONS,
                *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
                *DJANGO_BASE_DELETE_ONLY_ACTIONS,
                *PROJECT_ALL_ACTIONS,
                *PROJECT_CLASS_ALL_GET_ACTIONS,
                *PROJECT_LOCATION_ALL_GET_ACTIONS,
                *PROJECT_FINANCES_ALL_GET_ACTIONS,
                *PROJECT_GROUP_ALL_GET_ACTIONS,
                *SAP_COST_ALL_GET_ACTIONS,
                *PROJECT_NOTE_ALL_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # has edit permissions for projects nad notes only
        # and only specific project fields
        _type = obj._meta.model.__name__

        if view.action in [
            *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
            *DJANGO_BASE_READ_ONLY_ACTIONS,
            *DJANGO_BASE_DELETE_ONLY_ACTIONS,
            *DJANGO_BASE_CREATE_ONLY_ACTIONS,
            *PROJECT_NOTE_ALL_ACTIONS] and _type in [
            "Project", "Note"
        ]:
            if _type == "Project" and any(
                [
                    item
                    for item in request.data.keys()
                    if item
                    in [
                        "finances",
                        "name", #* Kohde/hanke Ei (No) # name
                        "hkrId", # * PW hanketunnus Ei (No) # hkrId
                        "type", # * Hanketyyppi Ei (No) # type
                        "entityName", # * Hankekokonaisuuden nimi Ei (No) #entityName
                        "sapProject", # * Projektinumero Ei (No) # sapProject
                        "sapNetwork", # * Verkkonumerot Ei (No) # sapNetwork
                        "programmed", # * Ohjelmoitu Ei (No) # programmed
                        "planningStartYear", # * Suunnittelun aloitusvuosi Ei (No) # planningStartYear
                        "constructionEndYear", # * Rakentamisen valmistumisvuosi Ei (No) # constructionEndYear
                        "category", # * Kategoria Ei (No) # category
                        "effectHousing", # * Vaikutus asuntotuotantoon Ei (No) # effectHousing
                        "riskAssessment", # * Riskiarvio Ei (No) # riskAssessment
                        "projectClass", # luokka: value can be masterClass/class/subClass
                        "costForecast",
                        "realizedCost", # * Toteumatiedot Ei (No) # realizedCost
                        "comittedCost", # * Sidotut Ei (No) # comittedCost
                        "spentCost", # * Käytetty Ei (No) # spentCost
                        "budgetOverrunYear", # ylistysoikeus vuosi Ei (No) # budgetOverrunYear
                        "budgetOverrunAmount", # * Ylitysoikeus Ei (No) # budgetOverrunAmount
                        "personPlanning", # * Vastuuhenkilö Ei (No) # personPlanning
                        "personConstruction", # * Rakennuttamisen vastuuhenkilö Ei (No) # personConstruction
                        "personProgramming", # * Ohjelmoija Ei (No) # personProgramming
                        "responsibleZone", # * Alueen vastuujaon mukaan Ei (No) # responsibleZone
                        "projectLocation", # value can be district/division/subDivision

                        # preliminaryBudgetDivision is not yet implemented in UI
                        #"preliminaryBudgetDivision", # * Kustannusarvion alustava jakautuminen Ei (No) # preliminaryBudgetDivision # ei löydy project.py
                ]
            ]):
                return False
            
            if _type == "Note":
                return True
            
            return True

        return True
    
class BaseProjectAreaPermissions(permissions.BasePermission):
    def project_belongs_to_808_main_class(self, obj: Project, request):
        projectClass = request.data.get("projectClass", None)
        try:
            projectClass = ProjectClass.objects.get(id=projectClass)
        except ProjectClass.DoesNotExist:
            projectClass = None

        if projectClass == None and obj.projectClass != None:
            projectClass = obj.projectClass

        return projectClass.path.startswith("8 08")

    def group_belongs_to_808_main_class(self, obj: ProjectGroup, request):
        groupClassRelation = request.data.get("classRelation", None)
        try:
            groupClassRelation = ProjectClass.objects.get(id=groupClassRelation)
        except ProjectClass.DoesNotExist:
            groupClassRelation = None

        if groupClassRelation == None and obj.classRelation != None:
            groupClassRelation = obj.classRelation

        return groupClassRelation.path.startswith("8 08")

class IsPlannerOfProjectAreas(BaseProjectAreaPermissions):
    def user_in_project_area_planner_group(self, request):
        if (
            "sg_kymp_sso_io_projektialueiden_ohjelmoijat"
            in request.user.ad_groups.all().values_list("name", flat=True)
        ):
            return True

    def has_permission(self, request, view):
        if (
            request.user.is_authenticated
            and self.user_in_project_area_planner_group(request=request)
            and request.method in SAFE_METHODS
            and view.action
            in [
                *DJANGO_BASE_READ_ONLY_ACTIONS,
                *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
                *DJANGO_BASE_CREATE_ONLY_ACTIONS,
                *DJANGO_BASE_DELETE_ONLY_ACTIONS,
                *PROJECT_CLASS_ALL_GET_ACTIONS,
                *PROJECT_LOCATION_ALL_GET_ACTIONS,
                *PROJECT_GROUP_ALL_ACTIONS,
                *PROJECT_ALL_ACTIONS,
                *PROJECT_FINANCES_ALL_GET_ACTIONS,
                *SAP_COST_ALL_GET_ACTIONS,
                *PROJECT_NOTE_ALL_ACTIONS
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        _type = obj._meta.model.__name__

        if view.action in [
            *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
            *DJANGO_BASE_DELETE_ONLY_ACTIONS,
            *DJANGO_BASE_CREATE_ONLY_ACTIONS,
            *DJANGO_BASE_READ_ONLY_ACTIONS,
            *PROJECT_NOTE_ALL_ACTIONS
        ] and _type in ["Project", "ProjectGroup", "Note"]:
            
            if _type == "Project":
                if self.project_belongs_to_808_main_class(
                    obj, request
                    ):
                    return True
        
            if _type == "ProjectGroup":
                if self.group_belongs_to_808_main_class(
                    obj, request
                ):
                    return True
            
            if _type == "Note":
                return True
        
        return False

class IsAdmin(permissions.BasePermission):
    def user_in_test_group(self, request):
        if "sg_kymp_sso_io_admin" in request.user.ad_groups.all().values_list(
            "name", flat=True
        ):
            return True

    def has_permission(self, request, view):
        if (
            request.user.is_authenticated
            and self.user_in_test_group(request=request)
            and request.method in SAFE_METHODS
            and view.action
            in [
                *DJANGO_BASE_READ_ONLY_ACTIONS,
                *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
                *DJANGO_BASE_CREATE_ONLY_ACTIONS,
                *DJANGO_BASE_DELETE_ONLY_ACTIONS,
                *PROJECT_CLASS_ALL_ACTIONS,
                *PROJECT_LOCATION_ALL_ACTIONS,
                *PROJECT_GROUP_ALL_ACTIONS,
                *PROJECT_FINANCES_ALL_ACTIONS,
                *PROJECT_ALL_ACTIONS,
                *SAP_COST_ALL_ACTIONS,
                *PROJECT_NOTE_ALL_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        _type = obj._meta.model.__name__ 
        return True

