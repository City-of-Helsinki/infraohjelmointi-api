from ..models import ProjectCategory


class ProjectCategoryService:
    @staticmethod
    def list_all() -> list[ProjectCategory]:
        return ProjectCategory.objects.all()
