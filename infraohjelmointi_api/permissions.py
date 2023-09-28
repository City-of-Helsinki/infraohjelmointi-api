from rest_framework import permissions
from infraohjelmointi_api.services.ADGroupService import ADGroupService

GET = "GET"
POST = "POST"
PATCH = "PATCH"
DELETE = "DELETE"
PUT = "PUT"
SAFE_METHODS = [GET, POST, PATCH, DELETE, PUT]
BASE_READ_ONLY_ACTIONS = ["list", "retrieve"]
BASE_UPDATE_ONLY_ACTIONS = [
    "update",
    "partial_update",
]
BASE_CREATE_ONLY_ACTIONS = ["create"]
BASE_DELETE_ONLY_ACTIONS = ["destroy"]
PROJECT_CLASS_CUSTOM_ACTIONS = [
    "get_coordinator_classes",
    "patch_coordinator_class_finances",
]
PROJECT_LOCATION_CUSTOM_ACTIONS = [
    "get_coordinator_locations",
    "patch_coordinator_location_finances",
]


class UserPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ["list", "retrieve"]:
            return request.user.is_authenticated

        return False

    # def has_object_permission(self, request, view, obj):
    #     return obj.user == request.user


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
                *BASE_READ_ONLY_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Viewer cannot edit anything or get an object instance
        return False


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
                *BASE_READ_ONLY_ACTIONS,
                *BASE_UPDATE_ONLY_ACTIONS,
                *BASE_CREATE_ONLY_ACTIONS,
                *BASE_DELETE_ONLY_ACTIONS,
                *PROJECT_CLASS_CUSTOM_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
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
                *BASE_READ_ONLY_ACTIONS,
                *BASE_UPDATE_ONLY_ACTIONS,
                *BASE_CREATE_ONLY_ACTIONS,
                *BASE_DELETE_ONLY_ACTIONS,
                PROJECT_CLASS_CUSTOM_ACTIONS[0],
                PROJECT_LOCATION_CUSTOM_ACTIONS[0],
            ]
        ):
            return True

        return False


class IsProgrammer(BaseProgrammerPlanner):
    def has_object_permission(self, request, view, obj):
        _type = obj._meta.model.__name__
        # Programmer cannot create a group
        if view.action in BASE_CREATE_ONLY_ACTIONS and _type == "ProjectGroup":
            return False
        # Programmers can edit and perform all other operations so return true for all other model instance actions
        return True


class IsPlanner(BaseProgrammerPlanner):
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
        # has edit permissions for projects only
        # and read permissions
        if (
            request.user.is_authenticated
            and self.user_in_project_manager_group(request=request)
            and request.method in [GET, PATCH]
            and view.action
            in [
                *BASE_READ_ONLY_ACTIONS,
                *BASE_UPDATE_ONLY_ACTIONS,
                PROJECT_CLASS_CUSTOM_ACTIONS[0],
                PROJECT_LOCATION_CUSTOM_ACTIONS[0],
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # has edit permissions for projects only
        # and specific project fields
        # Coordinators can edit and perform all operations so return true for all model instance actions
        _type = obj._meta.model.__name__
        if view.action in BASE_UPDATE_ONLY_ACTIONS and _type == "Project":
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
