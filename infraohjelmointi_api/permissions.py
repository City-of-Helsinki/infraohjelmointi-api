import logging
from infraohjelmointi_api.models.Project import Project
from infraohjelmointi_api.models.ProjectClass import ProjectClass
from infraohjelmointi_api.models.ProjectGroup import ProjectGroup
from rest_framework import permissions
from infraohjelmointi_api.services.ADGroupService import ADGroupService

logger = logging.getLogger("infraohjelmointi_api")

GET = "GET"
POST = "POST"
PATCH = "PATCH"
DELETE = "DELETE"
PUT = "PUT"
#OPTIONS = "OPTIONS"
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
PROJECT_NOTE_COORDINATOR_GET_ACTIONS = []
PROJECT_NOTE_PLANNING_GET_ACTIONS = ["get_note_history", "get_note_history_by_user"]
PROJECT_NOTE_ALL_GET_ACTIONS = [
    *PROJECT_NOTE_PLANNING_GET_ACTIONS,
    *PROJECT_NOTE_COORDINATOR_GET_ACTIONS,
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
]
PROJECT_PLANNING_GET_ACTIONS = [
    "get_projects_by_financial_year",
    "get_project_by_financial_year",
    "get_search_results",
    "get_project_notes",
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
SAP_COST_PLANNING_GET_ACTIONS = ["get_sap_costs_by_year"]
SAP_COST_COORDINATOR_GET_ACTIONS = ["get_sap_costs_by_year"]
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

#        "sg_kymp_sso_io_koordinaattorit": "86b826df-589c-40f9-898f-1584e80b5482",
#        "sg_kymp_sso_io_ohjelmoijat": "da48bfe9-6a99-481f-a252-077d31473c4c",
#        "sg_kymp_sso_io_projektialueiden_ohjelmoijat": "4d229780-b511-4652-b32b-362ad88a7b55",
#        "sg_kymp_sso_io_projektipaallikot": "31f86f09-b674-4c1d-81db-6d5fe2e587f9",
#        "sl_dyn_kymp_sso_io_katselijat": "7e39a13e-bd48-43ab-bd23-738e73b5137a",
#        "sg_kymp_sso_io_admin": "sg_kymp_sso_io_admin",

# katselijat
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
                *PROJECT_NOTE_PLANNING_GET_ACTIONS,
                *SAP_COST_PLANNING_GET_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Viewer cannot edit anything or get an object instance
        return False

# koordinaattorit
class IsCoordinator(permissions.BasePermission):
    def user_in_coordinator_group(self, request):
        if "sg_kymp_sso_io_koordinaattorit" in request.user.ad_groups.all().values_list(
            "name", flat=True
        ):
            return True

    def has_permission(self, request, view):
        if (
            request.user.is_authenticated
            and self.user_in_coordinator_group(request=request)
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
        logger.error("???")
        logging.ERROR("?????")
        logging.ERROR(obj._meta.model.__name__)

        _type = obj._meta.model.__name__
        # Coordinators can not ??
        # if view.action in DJANGO_BASE_UPDATE_ONLY_ACTIONS: #and _type == "ProjectGroup":
          #  return False
        # Coordinators can edit and perform all operations so return true for all model instance actions
        return True


class BaseProgrammerPlanner(permissions.BasePermission):
    def user_in_programmer_or_planning_group(self, request):
        if "sg_kymp_sso_io_ohjelmoijat" in request.user.ad_groups.all().values_list(
            "name", flat=True
        ):
            return True

    def has_permission(self, request, view):
        if (
            request.user.is_authenticated
            and self.user_in_programmer_or_planning_group(request=request)
            and request.method in SAFE_METHODS
            and view.action
            in [
                *DJANGO_BASE_READ_ONLY_ACTIONS,
                *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
                *DJANGO_BASE_CREATE_ONLY_ACTIONS,
                *DJANGO_BASE_DELETE_ONLY_ACTIONS,
                *PROJECT_CLASS_ALL_GET_ACTIONS,
                *PROJECT_LOCATION_ALL_GET_ACTIONS,
                *PROJECT_ALL_ACTIONS,
                *PROJECT_NOTE_ALL_ACTIONS,
                *PROJECT_GROUP_ALL_ACTIONS,
                *PROJECT_FINANCES_ALL_ACTIONS,
            ]
        ):
            return True

        return False 

# Ohjelmoijat 
class IsProgrammer(BaseProgrammerPlanner):
    #logger.error("???")
    def user_in_viewer_group(self, request):
        if "sg_dyn_kymp_sso_io_ohjelmoijat" in request.user.ad_groups.all().values_list(
            "name", flat=True
        ):
            return True
        
    def has_object_permission(self, request, view, obj):
        _type = obj._meta.model.__name__
        # Programmer cannot update/create a group
        if view.action in DJANGO_BASE_UPDATE_ONLY_ACTIONS and _type == "ProjectGroup":
            return False
        # Programmers can edit and perform all other operations so return true for all other model instance actions
        return True

# 
class IsPlanner(BaseProgrammerPlanner):
    def has_object_permission(self, request, view, obj):
        # Planners can edit and perform all operations so return true for all model instance actions
        return True

# projektipaallikot
class IsProjectManager(permissions.BasePermission):
    def user_in_project_manager_group(self, request):
        if (
            "sg_kymp_sso_io_projektipaallikot"
            in request.user.ad_groups.all().values_list("name", flat=True)
        ):
            return True

    def has_permission(self, request, view):
        # has edit permissions for projects only
        # and read permissions
        if (
            request.user.is_authenticated
            and self.user_in_project_manager_group(request=request)
            and request.method in [GET, PATCH]
            and view.action
            in [
                *DJANGO_BASE_READ_ONLY_ACTIONS,
                *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
                *PROJECT_ALL_ACTIONS,
                *PROJECT_CLASS_ALL_GET_ACTIONS,
                *PROJECT_LOCATION_ALL_GET_ACTIONS,
                *PROJECT_FINANCES_ALL_GET_ACTIONS,
                *PROJECT_GROUP_ALL_GET_ACTIONS,
                *PROJECT_NOTE_ALL_GET_ACTIONS,
                *SAP_COST_ALL_GET_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # has edit permissions for projects only
        # and specific project fields
        _type = obj._meta.model.__name__
        if view.action in DJANGO_BASE_UPDATE_ONLY_ACTIONS and _type in [
            "Project",
            "Note",
        ]:
            if any(
                [
                    item
                    for item in request.data.keys()
                    if item
                    in [
                        "finances",
                        "hkrId",
                        "type",
                        "name",
                        "masterPlanAreaNumber",
                        "trafficPlanNumber",
                        "bridgeNumber",
                        "sapProject",
                        "sapNetwork",
                        "programmed",
                        "planningStartYear",
                        "constructionEndYear",
                        "category",
                        "effectHousing",
                        "riskAssessment",
                        "projectClass",
                        "budget",
                        "projectCostForecast",
                        "planningCostForecast",
                        "constructionCostForecast",
                        "costForecast",
                        "personPlanning",
                        "personProgramming",
                        "personConstruction",
                        "projectLocation",
                    ]
                ]
            ):
                return False
            return True

        return False


class BaseProjectAreaPermissions(permissions.BasePermission):
    def project_belongs_to_808_main_class(self, obj: Project, request):
        projectClass = request.data.get("projectClass", None)
        try:
            projectClass = ProjectClass.objects.get(id=projectClass)
        except ProjectClass.DoesNotExist:
            projectClass = None

        if projectClass == None and obj.projectClass != None:
            projectClass = obj.projectClass
        else:
            return False

        return projectClass.path.startswith("8 08")

    def group_belongs_to_808_main_class(self, obj: ProjectGroup, request):
        groupClassRelation = request.data.get("classRelation", None)
        try:
            groupClassRelation = ProjectClass.objects.get(id=groupClassRelation)
        except ProjectClass.DoesNotExist:
            groupClassRelation = None

        if groupClassRelation == None and obj.classRelation != None:
            groupClassRelation = obj.classRelation
        else:
            return False

        return groupClassRelation.path.startswith("8 08")

    def patch_data_in_forbidden_non_808_main_class_project_fields(self, request):
        """
        Utility function to check if the fields being patched are permissible to be patched for a non 808 main class project.\n
        Returns true if patch data is not permissible to be patched.
        """
        return any(
            [
                item
                for item in request.data.keys()
                if item
                in [
                    "finances",
                    "hkrId",
                    "type",
                    "name",
                    "masterPlanAreaNumber",
                    "trafficPlanNumber",
                    "bridgeNumber",
                    "sapProject",
                    "sapNetwork",
                    "programmed",
                    "planningStartYear",
                    "constructionEndYear",
                    "category",
                    "effectHousing",
                    "riskAssessment",
                    "projectClass",
                    "budget",
                    "projectCostForecast",
                    "planningCostForecast",
                    "constructionCostForecast",
                    "costForecast",
                    "personPlanning",
                    "personProgramming",
                    "personConstruction",
                    "projectLocation",
                ]
            ]
        )

    def user_in_area_programmer_planner_group(self, request):
        if (
            "sg_kymp_sso_io_projektialueiden_ohjelmoijat"
            in request.user.ad_groups.all().values_list("name", flat=True)
        ):
            return True

# projektialueiden_ohjelmoijat
class IsProgrammerOfProjectAreas(BaseProjectAreaPermissions):
    def has_permission(self, request, view):
        if (
            request.user.is_authenticated
            and self.user_in_area_programmer_planner_group(request=request)
            and request.method in SAFE_METHODS
            and view.action
            in [
                *DJANGO_BASE_READ_ONLY_ACTIONS,
                *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
                *DJANGO_BASE_DELETE_ONLY_ACTIONS,
                *DJANGO_BASE_CREATE_ONLY_ACTIONS,
                *PROJECT_CLASS_ALL_GET_ACTIONS,
                *PROJECT_LOCATION_ALL_GET_ACTIONS,
                *PROJECT_GROUP_ALL_ACTIONS,
                *PROJECT_NOTE_ALL_ACTIONS,
                *PROJECT_ALL_ACTIONS,
                *PROJECT_FINANCES_ALL_GET_ACTIONS,
                *SAP_COST_ALL_GET_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        _type = obj._meta.model.__name__
        if view.action in [
            *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
            *DJANGO_BASE_DELETE_ONLY_ACTIONS,
        ] and _type in ["Project", "Note"]:
            if _type == "Project":
                if not self.project_belongs_to_808_main_class(obj, request) and (
                    request.action == "destroy"
                    or self.patch_data_in_forbidden_non_808_main_class_project_fields(
                        request
                    )
                ):
                    return False

            if _type == "Note" and request.action == "destroy":
                return False

            return True

        return False


class IsPlannerOfProjectAreas(BaseProjectAreaPermissions):
    def has_permission(self, request, view):
        if (
            request.user.is_authenticated
            and self.user_in_area_programmer_planner_group(request=request)
            and request.method in SAFE_METHODS
            and view.action
            in [
                *DJANGO_BASE_READ_ONLY_ACTIONS,
                *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
                *DJANGO_BASE_CREATE_ONLY_ACTIONS,
                *PROJECT_CLASS_ALL_GET_ACTIONS,
                *PROJECT_LOCATION_ALL_GET_ACTIONS,
                *PROJECT_GROUP_ALL_ACTIONS,
                *PROJECT_NOTE_ALL_ACTIONS,
                *PROJECT_ALL_ACTIONS,
                *PROJECT_FINANCES_ALL_GET_ACTIONS,
                *SAP_COST_ALL_GET_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        _type = obj._meta.model.__name__
        if view.action in DJANGO_BASE_UPDATE_ONLY_ACTIONS and _type in [
            "Project",
            "ProjectGroup",
            "Note",
        ]:
            if _type == "Project":
                if not self.project_belongs_to_808_main_class(
                    obj, request
                ) and self.patch_data_in_forbidden_non_808_main_class_project_fields(
                    request
                ):
                    return False

            if _type == "ProjectGroup":
                if not self.group_belongs_to_808_main_class(obj, request):
                    return False

            return True
        return False
