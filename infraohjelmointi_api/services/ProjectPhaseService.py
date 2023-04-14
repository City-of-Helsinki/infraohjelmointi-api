from ..models import ProjectPhase


class ProjectPhaseService:
    @staticmethod
    def list_all() -> list[ProjectPhase]:
        return ProjectPhase.objects.all()
