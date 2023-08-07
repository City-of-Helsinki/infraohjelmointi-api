from ..models import ProjectClass


class ProjectClassService:
    @staticmethod
    def get_or_create(
        name: str,
        parent: ProjectClass | None,
        path: str,
        forCoordinatorOnly: bool = False,
        relatedTo: ProjectClass = None,
    ) -> ProjectClass:
        return ProjectClass.objects.get_or_create(
            name=name,
            parent=parent,
            path=path,
            forCoordinatorOnly=forCoordinatorOnly,
            relatedTo=relatedTo,
        )

    @staticmethod
    def list_all() -> list[ProjectClass]:
        """List all project classes for programmer view"""
        return ProjectClass.objects.all().filter(forCoordinatorOnly=False)

    @staticmethod
    def list_all_for_coordinator() -> list[ProjectClass]:
        """List all project classes for coordinator view"""
        return ProjectClass.objects.all().filter(forCoordinatorOnly=True)

    @staticmethod
    def get_by_id(id: str) -> ProjectClass:
        """Get project class by id"""
        return ProjectClass.objects.get(id=id)

    @staticmethod
    def instance_exists(values: dict) -> ProjectClass:
        """Check if instance exists in DB"""
        return ProjectClass.objects.filter(**values).exists()
