from ..models import ProjectPhase


class ProjectPhaseService:
    @staticmethod
    def list_all() -> list[ProjectPhase]:
        return ProjectPhase.objects.all()

    @staticmethod
    def get_by_id(id: str) -> ProjectPhase:
        return ProjectPhase.objects.get(id=id)

    @staticmethod
    def get_by_value(value: str) -> ProjectPhase:
        return ProjectPhase.objects.get(value=value)
