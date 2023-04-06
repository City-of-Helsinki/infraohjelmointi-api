from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from infraohjelmointi_api.models import Project


class EstPlanningStartValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        estPlanningStart = allFields.get("estPlanningStart", None)
        if estPlanningStart is None:
            return

        project = serializer.instance
        estPlanningEnd = allFields.get("estPlanningEnd", None)

        if project is not None and hasattr(project, "lock"):
            planningStartYear = project.planningStartYear
            if planningStartYear is not None and estPlanningStart is not None:
                if estPlanningStart.year < planningStartYear:
                    raise ValidationError(
                        detail={
                            "estPlanningStart": "estPlanningStart date cannot be set to a earlier date than Start year of planning when project is locked"
                        },
                        code="estPlanningStart_et_planningStartYear_locked",
                    )
        if (
            estPlanningEnd is None
            and project is not None
            and project.estPlanningEnd is not None
        ):
            estPlanningEnd = project.estPlanningEnd

        if estPlanningEnd is not None and estPlanningStart is not None:
            if estPlanningStart > estPlanningEnd:
                raise ValidationError(
                    detail={
                        "estPlanningStart": "Date cannot be later than estPlanningEnd"
                    },
                    code="estPlanningStart_lt_estPlanningEnd",
                )
