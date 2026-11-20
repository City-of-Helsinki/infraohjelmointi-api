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


def get_planning_path(obj):
    instance_type = obj._meta.model.__name__
    class_instance = None
    location_instance = None
    if instance_type == "Project":
        group = getattr(obj, "projectGroup", None)
        class_instance = getattr(group, "classRelation", None) if group is not None else None
        location_instance = getattr(group, "locationRelation", None) if group is not None else None
        if class_instance is None:
            class_instance = getattr(obj, "projectClass", None)
        if location_instance is None:
            location_instance = getattr(obj, "projectLocation", None)
    elif instance_type == "ProjectClass":
        class_instance = obj
    elif instance_type == "ProjectLocation":
        class_instance = obj.parentClass
        location_instance = obj
    elif instance_type == "ProjectGroup":
        class_instance = getattr(obj, "classRelation", None)
        location_instance = getattr(obj, "locationRelation", None)

    path_params = {}
    current_class = class_instance
    visited_classes = set()
    while current_class is not None:
        class_id = str(current_class.id)
        if class_id in visited_classes:
            break
        visited_classes.add(class_id)
        param = _planning_class_param(current_class)
        if param is None:
            break
        path_params[param] = class_id
        current_class = current_class.parent

    if instance_type != "Project" and class_instance is None:
        return ""

    current_location = location_instance
    visited_locations = set()
    while current_location is not None:
        location_id = str(current_location.id)
        if location_id in visited_locations:
            break
        visited_locations.add(location_id)
        param = _planning_location_param(current_location)
        if param is None:
            break
        if param == "district":
            path_params[param] = location_id
            break
        current_location = current_location.parent

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
