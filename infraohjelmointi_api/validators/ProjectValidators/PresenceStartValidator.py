from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class PresenceStartValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)

        presenceStart = allFields.get("presenceStart", None)
        if presenceStart is None:
            return

        presenceEnd = allFields.get("presenceEnd", None)

        if (
            presenceEnd is None
            and project is not None
            and project.presenceEnd is not None
        ):
            presenceEnd = project.presenceEnd

        if presenceStart is not None and presenceEnd is not None:
            if presenceStart > presenceEnd:
                raise ValidationError(
                    detail={"presenceStart": "Date cannot be later than presenceEnd"},
                    code="presenceStart_lt_presenceEnd",
                )
