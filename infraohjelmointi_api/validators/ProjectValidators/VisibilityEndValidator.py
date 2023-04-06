from rest_framework.exceptions import ValidationError


class VisibilityEndValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        visibilityEnd = allFields.get("visibilityEnd", None)
        if visibilityEnd is None:
            return
        project = serializer.instance
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
