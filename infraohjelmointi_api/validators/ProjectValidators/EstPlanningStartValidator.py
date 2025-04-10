from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class EstPlanningStartValidator(BaseValidator):
    requires_context = True

    def __call__(self, all_fields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        project_id = all_fields.get("projectId", None)
        project = self.getProjectInstance(project_id, serializer=serializer)

        est_planning_start = all_fields.get("estPlanningStart", None)
        if (
            est_planning_start is None
            and project is not None
            and "estPlanningStart" not in all_fields
        ):
            est_planning_start = project.estPlanningStart

        if est_planning_start is None:
            return

        planning_start_year = all_fields.get("planningStartYear", None)
        if (
            planning_start_year is None
            and project is not None
            and "planningStartYear" not in all_fields
        ):
            planning_start_year = project.planningStartYear

        if planning_start_year is not None and est_planning_start is not None:
            if est_planning_start.year != planning_start_year:
                raise ValidationError(
                    detail={
                        "estPlanningStart": "estPlanningStart date cannot be set to a earlier or later date than Start year of planning"
                    },
                    code="estPlanningStart_df_planningStartYear",
                )

        est_planning_end = all_fields.get("estPlanningEnd", None)

        if (
            est_planning_end is None
            and project is not None
            and "estPlanningEnd" not in all_fields
        ):
            est_planning_end = project.estPlanningEnd

        if est_planning_end is not None and est_planning_start is not None:
            if est_planning_start > est_planning_end:
                raise ValidationError(
                    detail={
                        "estPlanningStart": "Date cannot be later than estPlanningEnd"
                    },
                    code="estPlanningStart_lt_estPlanningEnd",
                )
