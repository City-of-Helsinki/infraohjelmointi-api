from rest_framework.exceptions import ValidationError


class EstPlanningEndValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        estPlanningEnd = allFields.get("estPlanningEnd", None)
        if estPlanningEnd is None:
            return
        project = serializer.instance
        estPlanningStart = allFields.get("estPlanningStart", None)

        if (
            estPlanningStart is None
            and project is not None
            and project.estPlanningStart is not None
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
