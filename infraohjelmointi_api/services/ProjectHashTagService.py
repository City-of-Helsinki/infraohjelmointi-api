from ..models import ProjectHashTag


class ProjectHashTagService:
    @staticmethod
    def list_all() -> list[ProjectHashTag]:
        return ProjectHashTag.objects.all()

    @staticmethod
    def find_by_name(name: str) -> ProjectHashTag:
        return ProjectHashTag.objects.filter(value=name)
