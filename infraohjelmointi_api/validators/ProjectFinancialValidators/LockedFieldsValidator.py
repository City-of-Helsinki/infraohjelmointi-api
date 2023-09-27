from datetime import date
from infraohjelmointi_api.services.ProjectFinancialService import (
    ProjectFinancialService,
)
from rest_framework.exceptions import ValidationError


class LockedFieldsValidator:
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        projectFinancialInstance = serializer.instance

        # Check if project is locked and any locked fields are not being updated
        year = serializer.context.get("finance_year", date.today().year)
        if year is None:
            year = date.today().year
        yearToFieldMapping = (
            ProjectFinancialService.get_year_to_financial_field_names_mapping(
                start_year=year
            )
        )

        if hasattr(projectFinancialInstance.project, "lock"):
            lockedFields = [
                "value",
            ]
            for field in lockedFields:
                if allFields.get(field, None) is not None:
                    raise ValidationError(
                        detail={
                            yearToFieldMapping[
                                projectFinancialInstance.year
                            ]: "The field {} cannot be modified when the project is locked".format(
                                yearToFieldMapping[projectFinancialInstance.year]
                            )
                        },
                        code="project_locked",
                    )
