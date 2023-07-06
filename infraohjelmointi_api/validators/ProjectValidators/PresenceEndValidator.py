from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class PresenceEndValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)

        presenceEnd = allFields.get("presenceEnd", None)
        if (
            presenceEnd is None
            and project is not None
            and "presenceEnd" not in allFields
        ):
            presenceEnd = project.presenceEnd
        if presenceEnd is None:
            return

        presenceStart = allFields.get("presenceStart", None)

        if (
            presenceStart is None
            and project is not None
            and "presenceStart" not in allFields
        ):
            presenceStart = project.presenceStart

        if presenceEnd is not None and presenceStart is not None:
            if presenceEnd < presenceStart:
                raise ValidationError(
                    detail={"presenceEnd": "Date cannot be earlier than presenceStart"},
                    code="presenceEnd_et_presenceStart",
                )
