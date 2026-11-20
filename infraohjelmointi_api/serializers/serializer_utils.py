"""Shared utilities for serializers."""
import environ
from infraohjelmointi_api.models import Project
from infraohjelmointi_api.services.ProjectWiseService import (
    PWProjectNotFoundError,
    PWProjectResponseError,
    ProjectWiseService,
)

env = environ.Env()
env.escape_proxy = True


def _planning_class_param(class_instance):
    if class_instance is None or class_instance.forCoordinatorOnly:
        return None
    if class_instance.parent_id is None:
        return "masterClass"

    parent = class_instance.parent
    if parent is None or parent.forCoordinatorOnly:
        return None
    if parent.parent_id is None:
        return "class"

    grandparent = parent.parent
    if (
        grandparent is not None
        and not grandparent.forCoordinatorOnly
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


def _planning_instances(obj, instance_type):
    if instance_type == "Project":
        group = getattr(obj, "projectGroup", None)
        class_instance = getattr(group, "classRelation", None) if group is not None else None
        location_instance = getattr(group, "locationRelation", None) if group is not None else None
        if class_instance is None:
            class_instance = getattr(obj, "projectClass", None)
        if location_instance is None:
            location_instance = getattr(obj, "projectLocation", None)
        return class_instance, location_instance
    if instance_type == "ProjectClass":
        return obj, None
    if instance_type == "ProjectLocation":
        return obj.parentClass, obj
    if instance_type == "ProjectGroup":
        return getattr(obj, "classRelation", None), getattr(obj, "locationRelation", None)
    return None, None


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


def get_planning_path(obj):
    instance_type = obj._meta.model.__name__
    class_instance, location_instance = _planning_instances(obj, instance_type)
    if instance_type != "Project" and class_instance is None:
        return ""
    path_params = {}
    _add_planning_hierarchy_path(
        path_params,
        class_instance,
        _planning_class_param,
        {"masterClass", "class", "subClass"},
    )
    _add_planning_hierarchy_path(
        path_params,
        location_instance,
        _planning_location_param,
        {"district"},
        stop_param="district",
    )

    return "&".join(
        "{}={}".format(key, path_params[key])
        for key in ("masterClass", "class", "subClass", "district")
        if key in path_params
    )


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
