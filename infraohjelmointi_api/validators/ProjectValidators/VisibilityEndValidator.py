from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class VisibilityEndValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)

        visibilityEnd = allFields.get("visibilityEnd", None)
        if visibilityEnd is None:
            return

        visibilityStart = allFields.get("visibilityStart", None)

        if (
            visibilityStart is None
            and project is not None
            and project.visibilityStart is not None
        ):
            visibilityStart = project.visibilityStart

        if visibilityEnd is not None and visibilityStart is not None:
            if visibilityEnd < visibilityStart:
                raise ValidationError(
                    detail={
                        "visibilityEnd": "Date cannot be earlier than visibilityStart"
                    },
                    code="visibilityEnd_et_visibilityStart",
                )
