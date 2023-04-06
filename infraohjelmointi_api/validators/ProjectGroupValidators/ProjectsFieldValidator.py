from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from infraohjelmointi_api.models import Project


class ProjectsFieldValidator:
    """
    Validator for checking if project already exists to a group
    """

    def __call__(self, projectIds) -> None:
        if projectIds is not None and len(projectIds) > 0:
            for projectId in projectIds:
                project = get_object_or_404(Project, pk=projectId)
                if project.projectGroup is not None:
                    raise ValidationError(
                        detail={
                            "projects": "Project: {} with id: {} already belongs to the group: {} with id: {}".format(
                                project.name,
                                projectId,
                                project.projectGroup.name,
                                project.projectGroup_id,
                            )
                        },
                        code="project_in_group",
                    )
