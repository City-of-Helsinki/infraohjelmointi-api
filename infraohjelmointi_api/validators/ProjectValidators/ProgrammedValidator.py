from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class ProgrammedValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)
        programmed = allFields.get("programmed", None)

        if programmed is None and project is not None and "programmed" not in allFields:
            programmed = project.programmed
        if programmed is None:
            return

        category = allFields.get("category", None)
        phase = allFields.get("phase", None)
        if phase is None and project is not None and "phase" not in allFields:
            phase = project.phase
        if category is None and project is not None and "category" not in allFields:
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
        # programmed == True then check class and locations are filled in
