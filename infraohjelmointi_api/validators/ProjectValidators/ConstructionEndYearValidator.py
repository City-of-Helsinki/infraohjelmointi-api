from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class ConstructionEndYearValidator(BaseValidator):
    requires_context = True

    def __call__(self, all_fields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        project_id = all_fields.get("projectId", None)
        project = self.getProjectInstance(project_id, serializer=serializer)
        construction_end_year = all_fields.get("constructionEndYear", None)
        if (
            construction_end_year is None
            and project is not None
            and "constructionEndYear" not in all_fields
        ):
            construction_end_year = project.constructionEndYear
        
        if construction_end_year is None:
            return
        
        planning_start_year = all_fields.get("planningStartYear", None)

        if (
            planning_start_year is None
            and project is not None
            and "planningStartYear" not in all_fields
        ):
            planning_start_year = project.planningStartYear

        if construction_end_year is not None and planning_start_year is not None:
            if construction_end_year < int(planning_start_year):
                raise ValidationError(
                    detail={
                        "constructionEndYear": "Year cannot be earlier than planningStartYear"
                    },
                    code="constructionEndYear_et_planningStartYear",
                )

        est_construction_end = all_fields.get("estConstructionEnd", None)
        if (
            est_construction_end is None
            and project is not None
            and "estConstructionEnd" not in all_fields
        ):
            est_construction_end = project.estConstructionEnd

        if construction_end_year is not None and est_construction_end is not None:
            if est_construction_end.year != construction_end_year:
                raise ValidationError(
                    detail={
                        "constructionEndYear": "estConstructionEnd date cannot be set to a later or earlier date than End year of construction"
                    },
                    code="estConstructionEnd_df_constructionEndYear",
                )
