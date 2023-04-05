from rest_framework.exceptions import ValidationError


class VisibilityStartValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        visibilityStart = allFields.get("visibilityStart", None)
        if visibilityStart is None:
            return
        project = serializer.instance
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
                    detail="Date cannot be later than visibilityEnd",
                    code="visibilityStart_lt_visibilityEnd",
                )
