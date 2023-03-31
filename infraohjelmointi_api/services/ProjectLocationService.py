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
