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
    def list_all_for_programmer() -> list[ProjectClass]:
        return ProjectClass.objects.all().filter(forCoordinatorOnly=False)

    @staticmethod
    def list_all_for_coordinator() -> list[ProjectClass]:
        return ProjectClass.objects.all().filter(forCoordinatorOnly=True)
