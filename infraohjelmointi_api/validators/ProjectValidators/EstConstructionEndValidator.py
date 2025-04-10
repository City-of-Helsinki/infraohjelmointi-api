from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class EstConstructionEndValidator(BaseValidator):
    requires_context = True

    def __call__(self, all_fields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        project_id = all_fields.get("projectId", None)
        project = self.getProjectInstance(project_id, serializer=serializer)
        est_construction_end = all_fields.get("estConstructionEnd", None)
        if (
            est_construction_end is None
            and project is not None
            and "estConstructionEnd" not in all_fields
        ):
            est_construction_end = project.estConstructionEnd

        if est_construction_end is None:
            return

        construction_end_year = all_fields.get("constructionEndYear", None)
        if (
            construction_end_year is None
            and project is not None
            and "constructionEndYear" not in all_fields
        ):
            construction_end_year = project.constructionEndYear

        if construction_end_year is not None and est_construction_end is not None:
            if est_construction_end.year != construction_end_year:
                raise ValidationError(
                    detail={
                        "estConstructionEnd": "estConstructionEnd date cannot be set to a later or earlier date than End year of construction"
                    },
                    code="estConstructionEnd_df_constructionEndYear",
                )

        est_construction_start = all_fields.get("estConstructionStart", None)

        if (
            est_construction_start is None
            and project is not None
            and "estConstructionStart" not in all_fields
        ):
            est_construction_start = project.estConstructionStart

        if est_construction_start is not None and est_construction_end is not None:
            if est_construction_end < est_construction_start:
                raise ValidationError(
                    detail={
                        "estConstructionEnd": "Date cannot be earlier than estConstructionStart"
                    },
                    code="estConstructionEnd_et_estConstructionStart",
                )
            
        est_warranty_phase_start = all_fields.get("estWarrantyPhaseStart", None)

        if (
            est_warranty_phase_start is None
            and project is not None
            and "estWarrantyPhaseStart" not in all_fields
        ):
            est_warranty_phase_start = project.estWarrantyPhaseStart

        if est_warranty_phase_start is not None and est_construction_end is not None:
            if est_warranty_phase_start > est_construction_end:
                raise ValidationError(
                    detail={
                        "estConstructionEnd": "Date cannot be later than estWarrantyPhaseStart"
                    },
                    code="estWarrantyPhaseEnd_lt_estWarrantyPhaseStart",
                )
