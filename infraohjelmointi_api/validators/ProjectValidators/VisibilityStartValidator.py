from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class VisibilityStartValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)

        visibilityStart = allFields.get("visibilityStart", None)
        if visibilityStart is None:
            return

        visibilityEnd = allFields.get("visibilityEnd", None)

        if (
            visibilityEnd is None
            and project is not None
            and project.visibilityEnd is not None
        ):
            visibilityEnd = project.visibilityEnd

        if visibilityStart is not None and visibilityEnd is not None:
            if visibilityStart > visibilityEnd:
                raise ValidationError(
                    detail={
                        "visibilityStart": "Date cannot be later than visibilityEnd"
                    },
                    code="visibilityStart_lt_visibilityEnd",
                )
