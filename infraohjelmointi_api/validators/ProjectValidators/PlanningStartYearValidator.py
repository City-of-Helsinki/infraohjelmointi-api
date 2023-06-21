from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class PlanningStartYearValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)
        planningStartYear = allFields.get("planningStartYear", None)
        if (
            planningStartYear is None
            and project is not None
            and "planningStartYear" not in allFields
        ):
            planningStartYear = project.planningStartYear
        if planningStartYear is None:
            return

        constructionEndYear = allFields.get("constructionEndYear", None)

        if (
            constructionEndYear is None
            and project is not None
            and "constructionEndYear" not in allFields
        ):
            constructionEndYear = project.constructionEndYear

        if constructionEndYear is not None and planningStartYear is not None:
            if planningStartYear > int(constructionEndYear):
                raise ValidationError(
                    detail={
                        "planningStartYear": "Year cannot be later than constructionEndYear"
                    },
                    code="planningStartYear_lt_constructionEndYear",
                )
