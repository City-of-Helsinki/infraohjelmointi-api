from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class EstConstructionStartValidator(BaseValidator):
    requires_context = True

    def __call__(self, all_fields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required
        project_id = all_fields.get("projectId", None)
        project = self.getProjectInstance(project_id, serializer=serializer)

        est_construction_start = all_fields.get("estConstructionStart", None)
        if est_construction_start is None and project is not None:
            est_construction_start = project.estConstructionStart

        if est_construction_start is None:
            return

        est_construction_end = all_fields.get("estConstructionEnd", None)

        if (
            est_construction_end is None
            and project is not None
            and "estConstructionEnd" not in all_fields
        ):
            est_construction_end = project.estConstructionEnd

        if est_construction_end is not None and est_construction_start is not None:
            if est_construction_start > est_construction_end:
                raise ValidationError(
                    detail={
                        "estConstructionStart": "Date cannot be later than estConstructionEnd"
                    },
                    code="estConstructionStart_lt_estConstructionEnd",
                )
