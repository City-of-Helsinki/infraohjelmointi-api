from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class EstPlanningEndValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)
        estPlanningEnd = allFields.get("estPlanningEnd", None)
        if (
            estPlanningEnd is None
            and project is not None
            and "estPlanningEnd" not in allFields
        ):
            estPlanningEnd = project.estPlanningEnd
        if estPlanningEnd is None:
            return

        estPlanningStart = allFields.get("estPlanningStart", None)

        if (
            estPlanningStart is None
            and project is not None
            and "estPlanningStart" not in allFields
        ):
            estPlanningStart = project.estPlanningStart

        if estPlanningEnd is not None and estPlanningStart is not None:
            if estPlanningEnd < estPlanningStart:
                raise ValidationError(
                    detail={
                        "estPlanningEnd": "Date cannot be earlier than estPlanningStart"
                    },
                    code="estPlanningEnd_et_estPlanningStart",
                )
