from ..models import ProjectPhaseDetail


class ProjectPhaseDetailService:
    @staticmethod
    def list_all() -> list[ProjectPhaseDetail]:
        return ProjectPhaseDetail.objects.all()

    @staticmethod
    def get_by_id(id: str) -> ProjectPhaseDetail:
        return ProjectPhaseDetail.objects.get(id=id)

    @staticmethod
    def find_by_value(value: str, phase_value: str = None) -> ProjectPhaseDetail:
        """
        Find a ProjectPhaseDetail by its value string.
        Optionally filter by phase value for disambiguation.
        """
        qs = ProjectPhaseDetail.objects.filter(value=value)
        if phase_value:
            qs = qs.filter(projectPhase__value=phase_value)
        return qs.first()
