from rest_framework.exceptions import ValidationError
from ..util.is_projectClass_projectLocation_valid import (
    _is_projectClass_projectLocation_valid,
)


class ProjectClassValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        projectClass = allFields.get("projectClass", None)
        if projectClass is None:
            return
        project = serializer.instance
        projectLocation = allFields.get("projectLocation", None)

        if (
            projectLocation is None
            and project is not None
            and project.projectLocation is not None
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
