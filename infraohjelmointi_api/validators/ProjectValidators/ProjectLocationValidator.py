from infraohjelmointi_api.validators.util.is_projectClass_projectLocation_valid import (
    _is_projectClass_projectLocation_valid,
)
from rest_framework.exceptions import ValidationError


class ProjectLocationValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        projectLocation = allFields.get("projectLocation", None)
        if projectLocation is None:
            return
        project = serializer.instance
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
                "Location: {} with path: {} cannot be under the subClass: {}".format(
                    projectLocation.name,
                    projectLocation.path,
                    projectClass.name,
                ),
                code="projectLocation_invalid_projectClass",
            )
        return projectLocation
