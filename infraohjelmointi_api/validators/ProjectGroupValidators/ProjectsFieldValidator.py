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
                        detail="Project: {} with id: {} already belongs to the group: {} with id: {}".format(
                            project.name,
                            projectId,
                            project.projectGroup.name,
                            project.projectGroup_id,
                        ),
                        code="project_in_group",
                    )

    # def __repr__(self):
    #     return "<%s(start_date_field=%s, end_date_field=%s)>" % (
    #         self.__class__.__name__,
    #         smart_repr(self.start_date_field),
    #         smart_repr(self.end_date_field),
    #     )
