"""Shared utilities for serializers."""
from urllib.parse import urlencode
import environ
from infraohjelmointi_api.models import Project
from infraohjelmointi_api.services.ProjectClassService import ProjectClassService
from infraohjelmointi_api.services.ProjectWiseService import (
    PWProjectNotFoundError,
    PWProjectResponseError,
    ProjectWiseService,
)

env = environ.Env()
env.escape_proxy = True


def _planning_class_param(class_instance, area_planner=False):
    def is_visible(instance):
        return (
            instance is not None
            and not instance.forCoordinatorOnly
            and (not area_planner or instance.name.startswith(("808", "8 08")))
        )

    if not is_visible(class_instance):
        return None
    if class_instance.parent_id is None:
        return "masterClass"

    parent = class_instance.parent
    if not is_visible(parent):
        return None
    if parent.parent_id is None:
        return "class"

    grandparent = parent.parent
    if (
        is_visible(grandparent)
        and grandparent.parent_id is None
    ):
        return "subClass"
    return None


def _planning_location_param(location_instance):
    if location_instance is None or location_instance.forCoordinatorOnly:
        return None
    if location_instance.parent_id is None:
        return "district"

    parent = location_instance.parent
    if parent is None or parent.forCoordinatorOnly:
        return None
    if parent.parent_id is None:
        return "division"

    grandparent = parent.parent
    if (
        grandparent is not None
        and not grandparent.forCoordinatorOnly
        and grandparent.parent_id is None
    ):
        return "subDivision"
    return None


def _add_planning_hierarchy_path(path_params, instance, get_param, included_params, stop_param=None):
    visited = set()
    while instance is not None:
        instance_id = str(instance.id)
        if instance_id in visited:
            break
        visited.add(instance_id)
        param = get_param(instance)
        if param is None:
            break
        if param in included_params:
            path_params[param] = instance_id
        if param == stop_param:
            break
        instance = instance.parent


def get_project_detail_planning_path(project, user=None):
    group = project.projectGroup
    class_instance = group.classRelation if group and group.classRelation_id else project.projectClass
    location_instance = (
        group.locationRelation if group and group.locationRelation_id else project.projectLocation
    )
    area_planner = user is not None and ProjectClassService.is_project_area_planner(user)
    path_params = {}
    _add_planning_hierarchy_path(
        path_params, class_instance, lambda instance: _planning_class_param(instance, area_planner),
        {"masterClass", "class", "subClass"},
    )
    _add_planning_hierarchy_path(
        path_params, location_instance, _planning_location_param, {"district"}, stop_param="district"
    )
    return urlencode(path_params)


def get_pw_folder_link_for_project(project: Project, pw_service=None):
    """
    Get ProjectWise folder link for a project.
    
    Args:
        project: The project instance
        pw_service: Optional ProjectWiseService instance (will be initialized if None)
    
    Returns:
        The ProjectWise folder link or None if not available
    """
    if project.hkrId is None:
        return None
    
    if pw_service is None:
        pw_service = ProjectWiseService()
    
    try:
        pwInstanceId = pw_service.get_project_from_pw(
            id=project.hkrId
        ).get("instanceId", None)
        return env("PW_PROJECT_FOLDER_LINK").format(pwInstanceId)
    except (PWProjectNotFoundError, PWProjectResponseError):
        return None
