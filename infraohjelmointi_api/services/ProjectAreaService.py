from ..models import ProjectArea


class ProjectAreaService:
    @staticmethod
    def list_all() -> list[ProjectArea]:
        return ProjectArea.objects.all()

    @staticmethod
    def get_by_id(id: str) -> ProjectArea:
        return ProjectArea.objects.get(id=id)
