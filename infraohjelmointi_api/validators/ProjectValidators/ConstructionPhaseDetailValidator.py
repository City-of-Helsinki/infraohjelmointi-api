from rest_framework.exceptions import ValidationError


class ConstructionPhaseDetailValidator:

    requires_context = True

    def __call__(self, allFields, serializer) -> None:
        constructionPhaseDetail = allFields.get("constructionPhaseDetail", None)
        if constructionPhaseDetail is None:
            return
        project = serializer.instance
        phase = allFields.get("phase", None)
        if phase is None and project is not None:
            phase = project.phase

        if phase is None or phase.value != "construction":
            raise ValidationError(
                "constructionPhase detail cannot be populated if phase is not `construction`",
                code="constructionPhaseDetail_invalid_phase",
            )
