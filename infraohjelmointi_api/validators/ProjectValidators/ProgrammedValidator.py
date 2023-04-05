from rest_framework.exceptions import ValidationError


class ProgrammedValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        programmed = allFields.get("programmed", None)
        if programmed is None:
            return
        project = serializer.instance
        category = allFields.get("category", None)
        phase = allFields.get("phase", None)
        if phase is None and project is not None:
            phase = project.phase
        if category is None and project is not None:
            category = project.category

        if category is None and programmed == True:
            raise ValidationError(
                detail="category must be populated if programmed is `True`",
                code="programmed_true_missing_category",
            )
        if programmed == False and (phase is None or phase.value != "proposal"):
            raise ValidationError(
                detail="phase must be set to `proposal` if programmed is `False`",
                code="programmed_false_missing_phase",
            )
        if programmed == True and (phase is None or phase.value != "programming"):
            raise ValidationError(
                detail="phase must be set to `programming` if programmed is `True`",
                code="programmed_true_missing_phase",
            )
