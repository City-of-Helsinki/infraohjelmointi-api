from rest_framework.exceptions import ValidationError


class EstConstructionStartValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        estConstructionStart = allFields.get("estConstructionStart", None)
        if estConstructionStart is None:
            return
        project = serializer.instance
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
                    detail="Date cannot be later than estConstructionEnd",
                    code="estConstructionStart_lt_estConstructionEnd",
                )
