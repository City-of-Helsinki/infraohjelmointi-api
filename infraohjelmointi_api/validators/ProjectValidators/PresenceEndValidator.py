from rest_framework.exceptions import ValidationError


class PresenceEndValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        presenceEnd = allFields.get("presenceEnd", None)
        if presenceEnd is None:
            return
        project = serializer.instance

        presenceStart = allFields.get("presenceStart", None)

        if (
            presenceStart is None
            and project is not None
            and project.presenceStart is not None
        ):
            presenceStart = project.presenceStart

        if presenceEnd is not None and presenceStart is not None:
            if presenceEnd < presenceStart:
                raise ValidationError(
                    detail={"presenceEnd": "Date cannot be earlier than presenceStart"},
                    code="presenceEnd_et_presenceStart",
                )
