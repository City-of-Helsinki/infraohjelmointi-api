from ..models import ProjectType


class ProjectTypeService:
    @staticmethod
    def list_all() -> list[ProjectType]:
        return ProjectType.objects.all()

    @staticmethod
    def get_by_id(id: str) -> ProjectType:
        return ProjectType.objects.get(id=id)
