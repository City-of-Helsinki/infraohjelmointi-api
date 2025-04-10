from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class EstWarrantyPhaseStartValidator(BaseValidator):
    requires_context = True

    def __call__(self, all_fields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        project_id = all_fields.get("projectId", None)
        project = self.getProjectInstance(project_id, serializer=serializer)

        est_warranty_phase_start = all_fields.get("estWarrantyPhaseStart", None)
        if est_warranty_phase_start is None and project is not None:
            est_warranty_phase_start = project.estWarrantyPhaseStart

        if est_warranty_phase_start is None:
            return

        est_warranty_phase_end = all_fields.get("estWarrantyPhaseEnd", None)

        if (
            est_warranty_phase_end is None
            and project is not None
            and "estWarrantyPhaseEnd" not in all_fields
        ):
            est_warranty_phase_end = project.estWarrantyPhaseEnd

        if est_warranty_phase_end is not None and est_warranty_phase_start is not None:
            if est_warranty_phase_start > est_warranty_phase_end:
                raise ValidationError(
                    detail={
                        "estWarrantyPhaseStart": "Date cannot be later than estWarrantyPhaseEnd"
                    },
                    code="estWarrantyPhaseStart_lt_estWarrantyPhasenEnd",
                )
            
        est_construction_end = all_fields.get("estConstructionEnd", None)

        if (
            est_construction_end is None
            and project is not None
            and "estConstructionEnd" not in all_fields
        ):
            est_construction_end = project.estConstructionEnd

        if est_construction_end is not None and est_warranty_phase_start is not None:
            if est_warranty_phase_start < est_construction_end:
                raise ValidationError(
                    detail={
                        "estWarrantyPhaseStart": "Date cannot be earlier than estConstructionEnd"
                    },
                    code="estWarrantyPhaseStart_et_estConstructionEnd",
                )
            
        construction_end_year = all_fields.get("constructionEndYear", None)
        if (
            construction_end_year is None
            and project is not None
            and "constructionEndYear" not in all_fields
        ):
            construction_end_year = project.constructionEndYear

        if construction_end_year is not None and est_warranty_phase_start is not None:
                if est_warranty_phase_start.year < construction_end_year:
                    raise ValidationError(
                    detail={
                        "estWarrantyPhaseStart": "Year cannot be earlier than constructionEndYear"
                    },
                    code="estWarrantyPhaseStart_et_constructionEndYear",
                )
