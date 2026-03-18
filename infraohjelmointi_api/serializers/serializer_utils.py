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
