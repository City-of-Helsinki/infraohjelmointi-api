from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class ConstructionEndYearValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)
        constructionEndYear = allFields.get("constructionEndYear", None)
        if (
            constructionEndYear is None
            and project is not None
            and "constructionEndYear" not in allFields
        ):
            constructionEndYear = project.constructionEndYear
        if constructionEndYear is None:
            return
        planningStartYear = allFields.get("planningStartYear", None)

        if (
            planningStartYear is None
            and project is not None
            and "planningStartYear" not in allFields
        ):
            planningStartYear = project.planningStartYear

        if constructionEndYear is not None and planningStartYear is not None:
            if constructionEndYear < int(planningStartYear):
                raise ValidationError(
                    detail={
                        "constructionEndYear": "Year cannot be earlier than planningStartYear"
                    },
                    code="constructionEndYear_et_planningStartYear",
                )
