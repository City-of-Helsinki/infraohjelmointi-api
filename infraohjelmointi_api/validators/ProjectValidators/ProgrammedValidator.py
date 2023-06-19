from rest_framework.exceptions import ValidationError


class ProgrammedValidator:
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        programmed = allFields.get("programmed", None)
        project = serializer.instance
        if programmed is None and project is not None:
            programmed = project.programmed
        if programmed is None:
            return

        category = allFields.get("category", None)
        phase = allFields.get("phase", None)
        if phase is None and project is not None:
            phase = project.phase
        if category is None and project is not None:
            category = project.category

        if category is None and programmed == True:
            raise ValidationError(
                detail={
                    "programmed": "category must be populated if programmed is `True`"
                },
                code="programmed_true_missing_category",
            )
        if programmed == False and (
            phase is None or (phase.value not in ["proposal", "design"])
        ):
            raise ValidationError(
                detail={
                    "programmed": "phase must be set to `proposal` or `design` if programmed is `False`"
                },
                code="programmed_false_missing_phase",
            )
        if programmed == True and (
            phase is None or (phase.value in ["proposal", "design"])
        ):
            raise ValidationError(
                detail={
                    "programmed": "phase cannot be `proposal` or `design` if programmed is `True`"
                },
                code="programmed_true_missing_phase",
            )
