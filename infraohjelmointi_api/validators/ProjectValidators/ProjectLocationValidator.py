from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from infraohjelmointi_api.validators.util.is_projectClass_projectLocation_valid import (
    _is_projectClass_projectLocation_valid,
)
from rest_framework.exceptions import ValidationError


class ProjectLocationValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)

        projectLocation = allFields.get("projectLocation", None)
        if projectLocation is None:
            return

        projectClass = allFields.get("projectClass", None)

        if (
            projectClass is None
            and project is not None
            and project.projectClass is not None
        ):
            projectClass = project.projectClass
        if not _is_projectClass_projectLocation_valid(
            projectLocation=projectLocation, projectClass=projectClass
        ):
            raise ValidationError(
                detail={
                    "projectLocation": "Location: {} with path: {} cannot be under the subClass: {}".format(
                        projectLocation.name,
                        projectLocation.path,
                        projectClass.name,
                    )
                },
                code="projectLocation_invalid_projectClass",
            )
        return projectLocation
