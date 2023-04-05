from rest_framework.exceptions import ValidationError


class LockedFieldsValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:

        project = serializer.instance
        if hasattr(project, "lock"):
            lockedFields = [
                "phase",
                "planningStartYear",
                "constructionEndYear",
                "programmed",
                "projectClass",
                "projectLocation",
                "siteId",
                "realizedCost",
                "budgetOverrunAmount",
                "budgetForecast1CurrentYear",
                "budgetForecast2CurrentYear",
                "budgetForecast3CurrentYear",
                "budgetForecast4CurrentYear",
                "budgetProposalCurrentYearPlus0",
                "budgetProposalCurrentYearPlus1",
                "budgetProposalCurrentYearPlus2",
                "preliminaryCurrentYearPlus3",
                "preliminaryCurrentYearPlus4",
                "preliminaryCurrentYearPlus5",
                "preliminaryCurrentYearPlus6",
                "preliminaryCurrentYearPlus7",
                "preliminaryCurrentYearPlus8",
                "preliminaryCurrentYearPlus9",
                "preliminaryCurrentYearPlus10",
            ]
            for field in lockedFields:
                if allFields.get(field, None) is not None:
                    raise ValidationError(
                        "The field {} cannot be modified when the project is locked".format(
                            field
                        ),
                        code="project_locked",
                    )
