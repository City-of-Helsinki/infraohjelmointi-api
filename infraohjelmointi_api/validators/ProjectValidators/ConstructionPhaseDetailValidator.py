from infraohjelmointi_api.validators.ProjectValidators.BaseValidator import (
    BaseValidator,
)
from rest_framework.exceptions import ValidationError


class ConstructionPhaseDetailValidator(BaseValidator):
    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        # in case of multiple projects being patched at the same time
        # this is then required

        projectId = allFields.get("projectId", None)
        project = self.getProjectInstance(projectId, serializer=serializer)

        constructionPhaseDetail = allFields.get("constructionPhaseDetail", None)

        if (
            constructionPhaseDetail is None
            and project is not None
            and "constructionPhaseDetail" not in allFields
        ):
            constructionPhaseDetail = project.constructionPhaseDetail

        if constructionPhaseDetail is None:
            return

        phase = allFields.get("phase", None)
        if phase is None and project is not None and "phase" not in allFields:
            phase = project.phase

        if phase is None or phase.value != "construction":
            raise ValidationError(
                detail={
                    "constructionPhaseDetail": "constructionPhase detail cannot be populated if phase is not `construction`"
                },
                code="constructionPhaseDetail_invalid_phase",
            )
