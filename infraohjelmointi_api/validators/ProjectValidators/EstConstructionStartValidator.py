from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class EstConstructionStartValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)

        estConstructionStart = allFields.get("estConstructionStart", None)
        if estConstructionStart is None:
            return

        estConstructionEnd = allFields.get("estConstructionEnd", None)

        if (
            estConstructionEnd is None
            and project is not None
            and project.estConstructionEnd is not None
        ):
            estConstructionEnd = project.estConstructionEnd

        if estConstructionEnd is not None and estConstructionStart is not None:
            if estConstructionStart > estConstructionEnd:
                raise ValidationError(
                    detail={
                        "estConstructionStart": "Date cannot be later than estConstructionEnd"
                    },
                    code="estConstructionStart_lt_estConstructionEnd",
                )
