from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from infraohjelmointi_api.models import Project


class ProjectsFieldValidator:
    """
    Validator for checking if project already exists to a group
    """

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        projectIds = allFields.get("projects", None)
        if projectIds is not None and len(projectIds) > 0:
            # Get existing group instance if there is any
            # In case of a PATCH or POST request to a group
            # None if POST request for a new group
            group = serializer.instance
            for projectId in projectIds:
                project = get_object_or_404(Project, pk=projectId)
                if (
                    (
                        # PATCH request to existing group
                        # Check if a project is in a group which is not same as the group being patched
                        # Means a project is being assigned to this group which belongs to another group already
                        group is not None
                        and project.projectGroup is not None
                        and project.projectGroup.id != group.id
                    )
                    or
                    # POST request for new group
                    # A project in the request already belongs to another group
                    (group is None and project.projectGroup is not None)
                ):
                    raise ValidationError(
                        detail="Project: {} cannot be assigned to this group. It already belongs to group: {} with groupId: {}".format(
                            project.name,
                            project.projectGroup.name,
                            project.projectGroup_id,
                        ),
                        code="project_in_group",
                    )
