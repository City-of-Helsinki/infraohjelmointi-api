from ..models import ProjectTypeQualifier


class ProjectTypeQualifierService:
    @staticmethod
    def list_all() -> list[ProjectTypeQualifier]:
        return ProjectTypeQualifier.objects.all()

    @staticmethod
    def get_by_id(id: str) -> ProjectTypeQualifier:
        return ProjectTypeQualifier.objects.get(id=id)
