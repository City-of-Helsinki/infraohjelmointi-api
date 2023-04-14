from ..models import ProjectType


class ProjectTypeService:
    @staticmethod
    def list_all() -> list[ProjectType]:
        return ProjectType.objects.all()
