from ..models import ProjectClass, ProjectLocation, ProjectGroup, Project


class ProjectService:
    @staticmethod
    def get(
        name: str,
        projectClass: ProjectClass,
        projectLocation: ProjectLocation,
        projectGroup: ProjectGroup,
    ) -> Project:
        return Project.objects.get(
            name=name,
            projectClass=projectClass,
            projectLocation=projectLocation,
            projectGroup=projectGroup,
        )

    @staticmethod
    def create(
        name: str,
        description: str,
        projectClass: ProjectClass,
        projectLocation: ProjectLocation,
        projectGroup: ProjectGroup,
    ) -> Project:
        return Project.objects.create(
            name=name,
            projectClass=projectClass,
            projectLocation=projectLocation,
            projectGroup=projectGroup,
            description=description,
        )

    @staticmethod
    def list_with_non_null_hkr_id() -> list[Project]:
        return Project.objects.filter(hkrId__isnull=False)

    @staticmethod
    def get_by_hkr_id(hkr_id: str) -> Project:
        return Project.objects.get(hkrId=hkr_id)

    @staticmethod
    def findByGroup(group_id: str) -> list[Project]:
        return Project.objects.filter(projectGroup=group_id)
