from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError
from ..util.is_projectClass_projectLocation_valid import (
    _is_projectClass_projectLocation_valid,
)


class ProjectClassValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)

        projectClass = allFields.get("projectClass", None)
        if (
            projectClass is None
            and project is not None
            and "projectClass" not in allFields
        ):
            projectClass = project.projectClass
        if projectClass is None:
            return

        projectLocation = allFields.get("projectLocation", None)
        if (
            projectLocation is None
            and project is not None
            and "projectLocation" not in allFields
        ):
            projectLocation = project.projectLocation

        if not _is_projectClass_projectLocation_valid(
            projectLocation=projectLocation, projectClass=projectClass
        ):
            raise ValidationError(
                detail={
                    "projectClass": "subClass: {} with path: {} cannot have the location: {} under it.".format(
                        projectClass.name,
                        projectClass.path,
                        projectLocation.name,
                    )
                },
                code="projectClass_invalid_projectLocation",
            )
