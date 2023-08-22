from ..models import ProjectHashTag


class ProjectHashTagService:
    @staticmethod
    def list_all() -> list[ProjectHashTag]:
        return ProjectHashTag.objects.all()
