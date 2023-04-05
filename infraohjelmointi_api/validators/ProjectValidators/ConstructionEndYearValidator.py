from rest_framework.exceptions import ValidationError


class ConstructionEndYearValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        constructionEndYear = allFields.get("constructionEndYear", None)
        if constructionEndYear is None:
            return
        project = serializer.instance
        planningStartYear = allFields.get("planningStartYear", None)

        if (
            planningStartYear is None
            and project is not None
            and project.planningStartYear is not None
        ):
            planningStartYear = project.planningStartYear

        if constructionEndYear is not None and planningStartYear is not None:
            if constructionEndYear < int(planningStartYear):
                raise ValidationError(
                    detail="Year cannot be earlier than planningStartYear",
                    code="constructionEndYear_et_planningStartYear",
                )
