from rest_framework.exceptions import ValidationError


class PresenceStartValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        presenceStart = allFields.get("presenceStart", None)
        if presenceStart is None:
            return
        project = serializer.instance
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
