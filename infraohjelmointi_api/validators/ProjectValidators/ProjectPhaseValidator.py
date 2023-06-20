from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError

from datetime import datetime


class ProjectPhaseValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)

        phase = allFields.get("phase", None)
        if phase is None and project is not None:
            phase = project.phase

        if phase is None:
            return

        if phase.value == "programming":
            category = allFields.get("category", None)
            planningStartYear = allFields.get("planningStartYear", None)
            constructionEndYear = allFields.get("constructionEndYear", None)

            if planningStartYear is None and project is not None:
                planningStartYear = project.planningStartYear

            if category is None and project is not None:
                category = project.category

            if constructionEndYear is None and project is not None:
                constructionEndYear = project.constructionEndYear

            if planningStartYear is None or constructionEndYear is None:
                raise ValidationError(
                    detail={
                        "phase": "planningStartYear and constructionEndYear must be populated if phase is `programming`"
                    },
                    code="programming_phase_missing_dates",
                )
            if category is None:
                raise ValidationError(
                    detail={
                        "phase": "category must be populated if phase is `programming`"
                    },
                    code="programming_phase_missing_category",
                )

        if phase.value == "draftInitiation":
            estPlanningStart = allFields.get("estPlanningStart", None)
            estPlanningEnd = allFields.get("estPlanningEnd", None)
            personPlanning = allFields.get("personPlanning", None)

            if estPlanningStart is None and project is not None:
                estPlanningStart = project.estPlanningStart
            if estPlanningEnd is None and project is not None:
                estPlanningEnd = project.estPlanningEnd
            if personPlanning is None and project is not None:
                personPlanning = project.personPlanning

            if estPlanningStart is None or estPlanningEnd is None:
                raise ValidationError(
                    detail={
                        "phase": "estPlanningStart and estPlanningEnd must be populated if phase is `draftInitiation`"
                    },
                    code="draftInitiation_phase_missing_dates",
                )
            if personPlanning is None:
                raise ValidationError(
                    detail={
                        "phase": "personPlanning must be populated if phase is `draftInitiation`"
                    },
                    code="draftInitiation_phase_missing_personPlanning",
                )

        if phase.value == "construction":
            estConstructionStart = allFields.get("estConstructionStart", None)
            estConstructionEnd = allFields.get("estConstructionEnd", None)
            personConstruction = allFields.get("personConstruction", None)

            if estConstructionStart is None and project is not None:
                estConstructionStart = project.estConstructionStart
            if estConstructionEnd is None and project is not None:
                estConstructionEnd = project.estConstructionEnd
            if personConstruction is None and project is not None:
                personConstruction = project.personConstruction

            if estConstructionStart is None or estConstructionEnd is None:
                raise ValidationError(
                    detail={
                        "phase": "estConstructionStart and estConstructionEnd must be populated if phase is `construction`"
                    },
                    code="construction_phase_missing_dates",
                )
            if personConstruction is None:
                raise ValidationError(
                    detail={
                        "phase": "personConstruction must be populated if phase is `construction`"
                    },
                    code="construction_phase_missing_personConstruction",
                )
        if phase.value == "warrantyPeriod":
            estConstructionEnd = allFields.get("estConstructionEnd", None)

            if (
                estConstructionEnd is None
                and project is not None
                and project.estConstructionEnd is not None
            ):
                estConstructionEnd = project.estConstructionEnd

            if estConstructionEnd is not None:
                if datetime.today().date() < estConstructionEnd:
                    raise ValidationError(
                        detail={
                            "phase": "phase cannot be `warrantyPeriod` if current date is earlier than estConstructionEnd"
                        },
                        code="warrantyPeriod_phase_inconsistent_date",
                    )
