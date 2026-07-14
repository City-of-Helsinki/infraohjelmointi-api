from infraohjelmointi_api.models.Project import Project
from infraohjelmointi_api.models.ProjectClass import ProjectClass
from infraohjelmointi_api.models.ProjectGroup import ProjectGroup
from infraohjelmointi_api.models import ProjectProgrammer, ClassProgrammerAssignment
from rest_framework import permissions
from django.conf import settings


def get_restricted_programmer_group_name():
    """AD group name used for restricted programmers (IO-756)."""
    return getattr(
        settings,
        "RESTRICTED_PROGRAMMER_AD_GROUP",
        "sg_kymp_sso_io_rajoitetut_ohjelmoijat",
    )


def user_in_restricted_programmer_group(request):
    """True if the authenticated user is in the restricted programmer AD group."""
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return False
    return get_restricted_programmer_group_name() in request.user.ad_groups.all().values_list(
        "name", flat=True
    )


def _get_legacy_class_paths_from_email(user_email):
    """Resolve class paths via email → name → ProjectClass.defaultProgrammer (IO-756 fallback)."""
    if not user_email or "@" not in user_email:
        return set()
    parts = [p.strip() for p in user_email.split("@")[0].split(".") if p.strip()]
    if len(parts) < 2:
        return set()
    first_name, last_name = parts[0].capitalize(), parts[1].capitalize()
    if not first_name or not last_name:
        return set()
    programmer = ProjectProgrammer.objects.filter(
        firstName__iexact=first_name,
        lastName__iexact=last_name,
    ).first()
    if not programmer:
        return set()
    return set(
        ProjectClass.objects.filter(defaultProgrammer=programmer)
        .values_list("path", flat=True)
    )


def get_restricted_user_assigned_class_paths(user):
    """Project-class paths the restricted programmer is allowed to edit."""
    # 1. Primary: direct ClassProgrammerAssignment rows
    assigned_paths = set(
        ClassProgrammerAssignment.objects.filter(user=user)
        .values_list("project_class__path", flat=True)
    )
    # 2. Fallback: legacy email -> name matching onto ProjectClass.defaultProgrammer
    assigned_paths.update(_get_legacy_class_paths_from_email(getattr(user, "email", None)))
    return [p for p in assigned_paths if p]


def target_path_matches_assigned_paths(target_class_path, assigned_paths):
    """True if target equals or is a descendant of an assigned path (paths use '/')."""
    if not target_class_path:
        return False
    for path in assigned_paths:
        if target_class_path == path or target_class_path.startswith(path + "/"):
            return True
    return False

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
    "send_to_talpa",
]
DJANGO_BASE_REORDER_ONLY_ACTIONS = [
    "reorder"
]
DJANGO_BASE_CREATE_ONLY_ACTIONS = ["create"]
DJANGO_BASE_DELETE_ONLY_ACTIONS = ["destroy"]
DJANGO_BASE_DELETE_OR_CREATE_ACTIONS = [
    *DJANGO_BASE_CREATE_ONLY_ACTIONS,
    *DJANGO_BASE_DELETE_ONLY_ACTIONS
]

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
PROJECT_NOTE_BASIC_ACTIONS = ["create"]
PROJECT_NOTE_ALL_GET_ACTIONS = [
    *PROJECT_NOTE_PLANNING_GET_ACTIONS,
    *PROJECT_NOTE_COORDINATOR_GET_ACTIONS,
]
PROJECT_NOTE_ALL_ACTIONS = [*PROJECT_NOTE_ALL_GET_ACTIONS, *PROJECT_NOTE_BASIC_ACTIONS,]

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
PROJECT_FORCED_TO_FRAME_PATCH = [
    "patch_bulk_forced_to_frame",
]
PROJECT_ALL_PATCH_ACTIONS = [
    *PROJECT_COORDINATOR_PATCH_ACTIONS,
    *PROJECT_PLANNING_PATCH_ACTIONS,
]
PROJECT_ALL_ACTIONS = [*PROJECT_ALL_GET_ACTIONS, *PROJECT_ALL_PATCH_ACTIONS]

#### SAP COST CUSTOM ACTIONS ####
SAP_COST_PLANNING_GET_ACTIONS = ["get_sap_cost_by_year", "get_current_year_sap_cost_by_year"]
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

#### Construction handover custom actions ####
CONSTRUCTION_HANDOVER_GET_ACTIONS = ["get_construction_handovers"]
CONSTRUCTION_HANDOVER_POST_ACTIONS = ["transitions"]

#### Project programme custom actions ####
PROJECT_PROGRAMME_BASENAME = "projectProgrammes"
PROJECT_PROGRAMME_POST_ACTIONS = ["transitions", "section_transitions", "switch_type"]
PROJECT_PROGRAMME_READ_ACTIONS = [*DJANGO_BASE_READ_ONLY_ACTIONS, "get_by_project"]

#### Project change-history custom actions (IO-879) ####
# Per-project audit-log history powering the "Näytä muutoshistoria" UI.
# Read-only and scoped to a single project, so it is granted to every role
# that can view a project (including plain viewers and restricted programmers).
PROJECT_HISTORY_GET_ACTIONS = ["get_project_history"]

LIST_OF_DENIED_FIELDS_FOR_PROJECT_MANAGER = [
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
    "personProgramming", # * Ohjelmoija Ei (No) # personProgramming
    "responsibleZone", # * Alueen vastuujaon mukaan Ei (No) # responsibleZone
    "projectLocation", # value can be district/division/subDivision

    # preliminaryBudgetDivision is not yet implemented in UI
    #"preliminaryBudgetDivision", # * Kustannusarvion alustava jakautuminen Ei (No)
    # preliminaryBudgetDivision # ei löydy project.py
]

# ALL THE PERMISSION LOGIC GOES HERE, CAN BE REFACTORED LATER.
# THESE CLASSES CAN BE ADDED TO BaseViewSet.py To APPLY THE REQUIRED PERMISSIONS AND ROLES
# WORK STILL NEEDED

class IsViewer(permissions.BasePermission):
    def user_in_viewer_group(self, request):
        if "sl_dyn_kymp_sso_io_katselijat" in request.user.ad_groups.all().values_list(
            "name", flat=True
        ) or "sg_kymp_sso_io_katselijat_muut" in request.user.ad_groups.all().values_list(
            "name", flat=True
        ) or "az_kymp_asgd_u_infraohjelmointi_ulkopuoliset" in request.user.ad_groups.all().values_list(
            "name", flat=True
        ) or "952da398-75b3-404a-b274-c8f351d7f5a7" in request.user.ad_groups.all().values_list(
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
                *PROJECT_HISTORY_GET_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # Viewer can only access project object, to be able to see the project card
        _type = obj._meta.model.__name__

        if view.action in [*DJANGO_BASE_READ_ONLY_ACTIONS] and _type == "Project":
            return True

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
                *CONSTRUCTION_HANDOVER_GET_ACTIONS,
                *PROJECT_HISTORY_GET_ACTIONS,
                *CONSTRUCTION_HANDOVER_POST_ACTIONS,
                *PROJECT_PROGRAMME_POST_ACTIONS,
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
        # IO-756: restricted programmers must not inherit broader rights
        # via overlapping AD memberships; let IsClassProgrammer decide.
        if user_in_restricted_programmer_group(request):
            return False
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
                *CONSTRUCTION_HANDOVER_GET_ACTIONS,
                *PROJECT_HISTORY_GET_ACTIONS,
                *CONSTRUCTION_HANDOVER_POST_ACTIONS,
                *PROJECT_PROGRAMME_POST_ACTIONS,
            ]
        ):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if user_in_restricted_programmer_group(request):
            return False
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
        if user_in_restricted_programmer_group(request):
            return False
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
                *PROJECT_ALL_ACTIONS,
                *PROJECT_CLASS_ALL_GET_ACTIONS,
                *PROJECT_LOCATION_ALL_GET_ACTIONS,
                *PROJECT_FINANCES_ALL_GET_ACTIONS,
                *PROJECT_GROUP_ALL_GET_ACTIONS,
                *SAP_COST_ALL_GET_ACTIONS,
                *PROJECT_NOTE_ALL_ACTIONS,
                *CONSTRUCTION_HANDOVER_GET_ACTIONS,
                *PROJECT_HISTORY_GET_ACTIONS,
                *CONSTRUCTION_HANDOVER_POST_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if user_in_restricted_programmer_group(request):
            return False
        # Project managers can only transition project programmes back to DRAFT
        if getattr(view, "basename", None) == PROJECT_PROGRAMME_BASENAME and view.action == "transitions":
            return request.data.get("to") == "DRAFT"
        # has edit permissions for projects nad notes only
        # and only specific project fields
        _type = obj._meta.model.__name__

        if view.action in [
            *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
            *DJANGO_BASE_READ_ONLY_ACTIONS,
            *PROJECT_NOTE_ALL_ACTIONS,
            *CONSTRUCTION_HANDOVER_GET_ACTIONS] and _type in [
            "Project", "Note"
        ]:
            if _type == "Project" and any(
                [
                    item
                    for item in request.data.keys()
                    if item
                    in LIST_OF_DENIED_FIELDS_FOR_PROJECT_MANAGER
            ]):
                return False

            if _type == "Note":
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
        if user_in_restricted_programmer_group(request):
            return False
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
                *PROJECT_NOTE_ALL_ACTIONS,
                *PROJECT_HISTORY_GET_ACTIONS,
            ]
        ):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if user_in_restricted_programmer_group(request):
            return False
        _type = obj._meta.model.__name__

        if view.action in [
            *DJANGO_BASE_READ_ONLY_ACTIONS,
            *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
            *DJANGO_BASE_CREATE_ONLY_ACTIONS,
            *DJANGO_BASE_DELETE_ONLY_ACTIONS,
            *PROJECT_ALL_ACTIONS,
            *PROJECT_NOTE_ALL_ACTIONS,
        ] and _type in ["Project", "ProjectGroup", "Note"]:
            if (
                (_type == "Project" and self.project_belongs_to_808_main_class(obj, request))
                or (_type == "ProjectGroup" and self.group_belongs_to_808_main_class(obj, request))
            ):
                return True

            elif _type == "Note":
                return True

            elif _type == "Project" and view.action not in [*DJANGO_BASE_DELETE_OR_CREATE_ACTIONS] and not any(
                [
                    item
                    for item in request.data.keys()
                    if item
                    in LIST_OF_DENIED_FIELDS_FOR_PROJECT_MANAGER
                ]):
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
                *DJANGO_BASE_REORDER_ONLY_ACTIONS,
                *DJANGO_BASE_CREATE_ONLY_ACTIONS,
                *DJANGO_BASE_DELETE_ONLY_ACTIONS,
                *PROJECT_CLASS_ALL_ACTIONS,
                *PROJECT_LOCATION_ALL_ACTIONS,
                *PROJECT_GROUP_ALL_ACTIONS,
                *PROJECT_FINANCES_ALL_ACTIONS,
                *PROJECT_ALL_ACTIONS,
                *SAP_COST_ALL_ACTIONS,
                *PROJECT_NOTE_ALL_ACTIONS,
                *PROJECT_FORCED_TO_FRAME_PATCH,
                *CONSTRUCTION_HANDOVER_GET_ACTIONS,
                *PROJECT_HISTORY_GET_ACTIONS,
                *CONSTRUCTION_HANDOVER_POST_ACTIONS,
                *PROJECT_PROGRAMME_POST_ACTIONS,
            ]
        ):
            return True
        return False

    def has_object_permission(self, request, view, obj):
        _type = obj._meta.model.__name__
        return True


class IsClassProgrammer(permissions.BasePermission):
    """
    Permission class for restricted class programmers (IO-756).

    Allows programmers to edit only projects in their specifically assigned classes.
    Similar to IsPlannerOfProjectAreas but with individual class-level restrictions.

    Users must be in the restricted programmer AD group and have a ProjectProgrammer
    assignment to edit projects. They can only edit projects where the projectClass
    matches their assignment.

    Coordinators and admins bypass these restrictions.
    """

    def user_in_restricted_programmer_group(self, request):
        """Check if user is in restricted programmer AD group"""
        return user_in_restricted_programmer_group(request)

    def user_is_coordinator_or_admin(self, request):
        """Check if user is coordinator or admin (bypass restrictions)"""
        ad_groups = request.user.ad_groups.all().values_list("name", flat=True)
        return (
            "sg_kymp_sso_io_koordinaattorit" in ad_groups
            or "sg_kymp_sso_io_admin" in ad_groups
        )

    def get_user_assigned_classes_paths(self, request):
        """Get project class paths assigned to this user."""
        return get_restricted_user_assigned_class_paths(request.user)

    def has_permission(self, request, view):
        """Check if user has permission for the action"""
        # Only apply to authenticated users
        if not request.user.is_authenticated:
            return False

        # Coordinators and admins bypass restrictions (let other classes handle)
        if self.user_is_coordinator_or_admin(request):
            return False

        # Only apply to restricted programmer group
        if not self.user_in_restricted_programmer_group(request):
            return False

        # Allow read actions
        if view.action in [
            *DJANGO_BASE_READ_ONLY_ACTIONS,
            *PROJECT_ALL_GET_ACTIONS,
            *PROJECT_CLASS_ALL_GET_ACTIONS,
            *PROJECT_LOCATION_ALL_GET_ACTIONS,
            *PROJECT_FINANCES_ALL_GET_ACTIONS,
            *PROJECT_GROUP_ALL_GET_ACTIONS,
            *SAP_COST_ALL_GET_ACTIONS,
            *PROJECT_NOTE_ALL_GET_ACTIONS,
            *PROJECT_HISTORY_GET_ACTIONS,
        ]:
            return True

        # Allow edit actions (will be checked at object level, except
        # patch_bulk_projects which is enforced inside the view).
        if view.action in [
            *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
            *PROJECT_NOTE_ALL_ACTIONS,
            "patch_bulk_projects",
            *PROJECT_PROGRAMME_POST_ACTIONS,
        ]:
            return True

        return False

    def _get_target_class_path_for_restricted_edit(self, obj):
        """Resolve project class path for restricted programmer object checks."""
        _type = obj._meta.model.__name__
        if _type == "Project":
            return obj.projectClass.path if obj.projectClass else None
        if _type == "Note":
            target_project = obj.project
            if target_project and target_project.projectClass:
                return target_project.projectClass.path
            return None
        if _type == "ProjectGroup":
            return obj.classRelation.path if obj.classRelation else None
        if _type == "ProjectProgramme":
            project = getattr(obj, "project", None)
            if project and project.projectClass:
                return project.projectClass.path
            return None
        return None

    @staticmethod
    def _target_path_matches_assigned_paths(target_class_path, assigned_paths):
        """True if target equals or is a child of an assigned path (paths use '/')."""
        return target_path_matches_assigned_paths(target_class_path, assigned_paths)

    def has_object_permission(self, request, view, obj):
        """Check if user has permission for this specific object"""
        if self.user_is_coordinator_or_admin(request):
            return True

        if view.action in DJANGO_BASE_READ_ONLY_ACTIONS:
            return True

        target_class_path = self._get_target_class_path_for_restricted_edit(obj)
        if not target_class_path:
            return False

        assigned_paths = self.get_user_assigned_classes_paths(request)
        if not assigned_paths:
            return False

        return self._target_path_matches_assigned_paths(
            target_class_path, assigned_paths
        )
    
class IsConstructionManagementLead(permissions.BasePermission):
    """Permission class for construction management leads (Rakennuttamisen esihenkilöt)."""

    CONSTRUCTION_HANDOVER_BASENAME = "constructionHandovers"

    def user_in_construction_management_lead_group(self, request):
        if (
            "sg_kymp_sso_io_rakennuttamisen_esihenkilot"
            in request.user.ad_groups.all().values_list("name", flat=True)
        ):
            return True
        else:
            return False

    def _is_construction_handover_view(self, view):
        return getattr(view, "basename", None) == self.CONSTRUCTION_HANDOVER_BASENAME

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not self.user_in_construction_management_lead_group(request=request):
            return False

        if request.method not in SAFE_METHODS:
            return False

        # Allow read rights for all resources this role can view.
        if request.method == GET and view.action in [
            *DJANGO_BASE_READ_ONLY_ACTIONS,
            *PROJECT_CLASS_ALL_GET_ACTIONS,
            *PROJECT_LOCATION_ALL_GET_ACTIONS,
            *PROJECT_GROUP_ALL_GET_ACTIONS,
            *PROJECT_FINANCES_ALL_GET_ACTIONS,
            *PROJECT_ALL_GET_ACTIONS,
            *SAP_COST_ALL_GET_ACTIONS,
            *CONSTRUCTION_HANDOVER_GET_ACTIONS,
        ]:
            return True

        # Strict write rights: only update/transition actions on construction handovers.
        if self._is_construction_handover_view(view) and view.action in [
            *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
            *CONSTRUCTION_HANDOVER_POST_ACTIONS,
        ]:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if request.method == GET:
            return True

        if self._is_construction_handover_view(view):
            return True

        return False


class IsProjectProgrammeContributor(permissions.BasePermission):
    """
    Permission class for project programme contributors.

    Editors (PROJECT_PROGRAMME_EDITOR_AD_GROUPS): users related to the project
    via personPlanning, personProgramming, or otherPersons can create, edit, and
    transition project programmes and sections to COMPLETE.

    Reverters (PROJECT_PROGRAMME_REVERTER_AD_GROUPS): can read all project
    programmes and transition any programme back to DRAFT.
    """

    _EDITOR_WRITE_ACTIONS = [
        *DJANGO_BASE_CREATE_ONLY_ACTIONS,
        *DJANGO_BASE_UPDATE_ONLY_ACTIONS,
        "transitions",
        "section_transitions",
        "switch_type",
    ]

    def _get_editor_groups(self):
        return getattr(settings, "PROJECT_PROGRAMME_EDITOR_AD_GROUPS", [])

    def _get_reverter_groups(self):
        return getattr(settings, "PROJECT_PROGRAMME_REVERTER_AD_GROUPS", [])

    def _get_user_ad_group_names(self, user):
        return set(user.ad_groups.all().values_list("name", flat=True))

    def _user_is_editor(self, user):
        editor_groups = self._get_editor_groups()
        if not editor_groups:
            return False
        return bool(set(editor_groups) & self._get_user_ad_group_names(user))

    def _user_is_reverter(self, user):
        reverter_groups = self._get_reverter_groups()
        if not reverter_groups:
            return False
        return bool(set(reverter_groups) & self._get_user_ad_group_names(user))

    def _user_is_related_to_project(self, user, project):
        """Check if user is related to the project via person relationships (email-based)."""
        if not user.email:
            return False
        user_email = user.email.lower()

        if project.personPlanning and project.personPlanning.email:
            if project.personPlanning.email.lower() == user_email:
                return True

        if project.personProgramming:
            person = getattr(project.personProgramming, "person", None)
            if person and person.email and person.email.lower() == user_email:
                return True

        for other_person in project.otherPersons.all():
            if other_person.email and other_person.email.lower() == user_email:
                return True

        return False

    def _user_is_related_to_programme(self, user, programme):
        project = getattr(programme, "project", None)
        if project is None:
            return False
        return self._user_is_related_to_project(user, project)

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if getattr(view, "basename", None) != PROJECT_PROGRAMME_BASENAME:
            return False

        if request.method not in SAFE_METHODS:
            return False

        is_editor = self._user_is_editor(request.user)
        is_reverter = self._user_is_reverter(request.user)

        if not is_editor and not is_reverter:
            return False

        # Read actions: allowed for both editors and reverters
        if view.action in PROJECT_PROGRAMME_READ_ACTIONS:
            return True

        # Create: editor only, relatedness checked via project in request body
        if view.action == "create":
            if not is_editor:
                return False
            project_id = request.data.get("project")
            if not project_id:
                return False
            from infraohjelmointi_api.models import Project as _Project
            try:
                project = _Project.objects.get(id=project_id)
            except (_Project.DoesNotExist, Exception):
                return False
            return self._user_is_related_to_project(request.user, project)

        # Write actions: editors only (object-level relatedness in has_object_permission)
        if is_editor and view.action in self._EDITOR_WRITE_ACTIONS:
            return True

        # Transitions to DRAFT: reverters only (direction enforced in has_object_permission)
        if is_reverter and view.action == "transitions":
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if getattr(view, "basename", None) != PROJECT_PROGRAMME_BASENAME:
            return False

        is_editor = self._user_is_editor(request.user)
        is_reverter = self._user_is_reverter(request.user)

        if not is_editor and not is_reverter:
            return False

        # Read actions: allow all for both roles
        if view.action in DJANGO_BASE_READ_ONLY_ACTIONS:
            return True

        # Transitions: editors can do any direction if related; reverters only DRAFT
        if view.action == "transitions":
            if is_editor:
                return self._user_is_related_to_programme(request.user, obj)
            if is_reverter:
                return request.data.get("to") == "DRAFT"

        # Remaining write actions: editors must be related to the project
        if is_editor:
            return self._user_is_related_to_programme(request.user, obj)

        return False
