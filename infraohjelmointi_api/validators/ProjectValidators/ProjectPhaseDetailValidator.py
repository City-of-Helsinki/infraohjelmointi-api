from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class ProjectPhaseDetailValidator(BaseValidator):
    """Validates that phaseDetail belongs to the project's current phase."""

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)

        phaseDetail = allFields.get("phaseDetail", None)

        if (
            phaseDetail is None
            and project is not None
            and "phaseDetail" not in allFields
        ):
            phaseDetail = project.phaseDetail

        if phaseDetail is None:
            return

        phase = allFields.get("phase", None)
        if phase is None and project is not None and "phase" not in allFields:
            phase = project.phase

        if phase is None:
            raise ValidationError(
                detail={
                    "phaseDetail": "Phase detail cannot be set without a phase"
                },
                code="phaseDetail_missing_phase",
            )

        if hasattr(phaseDetail, "projectPhase") and phaseDetail.projectPhase != phase:
            raise ValidationError(
                detail={
                    "phaseDetail": f"Phase detail does not belong to the selected phase '{phase.value}'"
                },
                code="phaseDetail_invalid_phase",
            )
