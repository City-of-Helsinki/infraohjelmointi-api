from rest_framework.exceptions import ValidationError


class PlanningStartYearValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        planningStartYear = allFields.get("planningStartYear", None)
        if planningStartYear is None:
            return
        project = serializer.instance
        constructionEndYear = allFields.get("constructionEndYear", None)

        if (
            constructionEndYear is None
            and project is not None
            and project.constructionEndYear is not None
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
