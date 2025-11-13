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
        projectClass = allFields.get("projectClass", None)

        if programmed is None and project is not None and "programmed" not in allFields:
            programmed = project.programmed

        if programmed is None:
            return

        if (
            projectClass is None
            and project is not None
            and "projectClass" not in allFields
        ):
            projectClass = project.projectClass

        category = allFields.get("category", None)
        phase = allFields.get("phase", None)
        if phase is None and project is not None and "phase" not in allFields:
            phase = project.phase

        if programmed == True and (
            phase is None or (phase.value in ["proposal", "design"])
        ):
            # Set programmed to false if phase is proposal or design
            # Since phase is changed from the planning view and field validations are not in effect on the view
            allFields["programmed"] = False
            programmed = False

        if category is None and project is not None and "category" not in allFields:
            category = project.category

        if category is None and programmed == True:
            raise ValidationError(
                detail={
                    "programmed": "category must be populated if programmed is `True`"
                },
                code="programmed_true_missing_category",
            )
        # IO-755: Allow programmed=False for completed phase (when no budget)
        if programmed == False and (
            phase is not None and (phase.value not in ["proposal", "design", "completed"])
        ):
            raise ValidationError(
                detail={
                    "programmed": "phase must be set to `proposal`, `design`, or `completed` if programmed is `False`"
                },
                code="programmed_false_missing_phase",
            )

        if programmed == True and projectClass is None:
            raise ValidationError(
                detail={
                    "programmed": "projectClass must be populated if programmed is `True`"
                },
                code="programmed_true_missing_projectClass",
            )
