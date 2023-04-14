from ..models import ProjectClass, ProjectLocation


class ProjectLocationService:
    @staticmethod
    def get_or_create(
        name: str,
        parent: ProjectLocation | None,
        path: str,
        parentClass: ProjectClass,
        relatedTo: ProjectLocation = None,
        forCoordinatorOnly: bool = False,
    ) -> ProjectLocation:
        return ProjectLocation.objects.get_or_create(
            name=name,
            parent=parent,
            path=path,
            parentClass=parentClass,
            relatedTo=relatedTo,
            forCoordinatorOnly=forCoordinatorOnly,
        )

    @staticmethod
    def list_all() -> list[ProjectLocation]:
        """List all project locations for programmer view"""
        return ProjectLocation.objects.all().filter(forCoordinatorOnly=False)

    @staticmethod
    def list_all_for_coordinator() -> list[ProjectLocation]:
        """List all project locations for coordinator view"""
        return ProjectLocation.objects.all().filter(forCoordinatorOnly=True)

    @staticmethod
    def find_by_path(path: str) -> list[ProjectLocation]:
        """Find all project locations by path for programmer view"""
        return list(
            ProjectLocation.objects.all().filter(path=path, forCoordinatorOnly=False)
        )

    def list_all_for_programmer() -> list[ProjectClass]:
        return ProjectLocation.objects.all().filter(forCoordinatorOnly=False)

    @staticmethod
    def list_all_for_coordinator() -> list[ProjectClass]:
        return ProjectLocation.objects.all().filter(forCoordinatorOnly=True)
