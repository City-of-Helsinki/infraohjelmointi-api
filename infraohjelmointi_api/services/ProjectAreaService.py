from ..models import ProjectArea


class ProjectAreaService:
    @staticmethod
    def list_all() -> list[ProjectArea]:
        return ProjectArea.objects.all()
