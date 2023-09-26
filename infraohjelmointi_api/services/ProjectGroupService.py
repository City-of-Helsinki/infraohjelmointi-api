from ..models import ProjectClass, ProjectLocation, ProjectGroup


class ProjectGroupService:
    @staticmethod
    def get_or_create(
        name: str,
        locationRelation: ProjectLocation,
        classRelation: ProjectClass,
    ) -> ProjectGroup:
        return ProjectGroup.objects.get_or_create(
            name=name,
            locationRelation=locationRelation,
            classRelation=classRelation,
        )
