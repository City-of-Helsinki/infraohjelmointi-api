from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class EstConstructionEndValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)
        estConstructionEnd = allFields.get("estConstructionEnd", None)
        if (
            estConstructionEnd is None
            and project is not None
            and "estConstructionEnd" not in allFields
        ):
            estConstructionEnd = project.estConstructionEnd

        if estConstructionEnd is None:
            return

        constructionEndYear = allFields.get("constructionEndYear", None)
        if (
            constructionEndYear is None
            and project is not None
            and "constructionEndYear" not in allFields
        ):
            constructionEndYear = project.constructionEndYear

        if project is not None and hasattr(project, "lock"):
            if constructionEndYear is not None and estConstructionEnd is not None:
                if estConstructionEnd.year > constructionEndYear:
                    raise ValidationError(
                        detail={
                            "estConstructionEnd": "estConstructionEnd date cannot be set to a later date than End year of construction when project is locked"
                        },
                        code="estConstructionEnd_lt_constructionEndYear_locked",
                    )

        estConstructionStart = allFields.get("estConstructionStart", None)

        if (
            estConstructionStart is None
            and project is not None
            and "estConstructionStart" not in allFields
        ):
            estConstructionStart = project.estConstructionStart

        if estConstructionStart is not None and estConstructionEnd is not None:
            if estConstructionEnd < estConstructionStart:
                raise ValidationError(
                    detail={
                        "estConstructionEnd": "Date cannot be earlier than estConstructionStart"
                    },
                    code="estConstructionEnd_et_estConstructionStart",
                )
