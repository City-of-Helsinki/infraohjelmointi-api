from ..models import ProjectClass, ProjectLocation, ProjectGroup, Project
from .ProjectClassService import ProjectClassService


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
    def find_by_group_id(group_id: str) -> list[Project]:
        return Project.objects.filter(projectGroup=group_id)

    @staticmethod
    def get_project_class_location_group_relations(project: Project) -> dict:
        """
        Get all levels of planning and coordination class/location and group relations linked to the provided project.

            Parameters
            ----------
            project : Project
                The project instance used to get related class/location/group relations

            Returns
            -------
            dict
               {
                "coordination": {
                    "masterClass": <ProjectClass instance>,
                    "class": <ProjectClass instance>,
                    "subClass": <ProjectClass instance>,
                    "collectiveSubLevel": <ProjectClass instance>,
                    "district": <ProjectLocation instance>,
                },
                "planning": {
                    "masterClass": <ProjectClass instance>,
                    "class": <ProjectClass instance>,
                    "subClass": <ProjectClass instance>,
                    "district": <ProjectLocation instance>,
                    "group": <ProjectGroup instance>,
                    },
                }
        """
        projectRelations = {
            "planning": {
                "masterClass": None,
                "class": None,
                "subClass": None,
                "district": None,
                "group": None,
            },
            "coordination": {
                "masterClass": None,
                "class": None,
                "subClass": None,
                "collectiveSubLevel": None,
                "district": None,
            },
        }

        projectRelations["planning"]["masterClass"] = (
            (
                project.projectClass
                if project.projectClass.parent is None
                else project.projectClass.parent
                if project.projectClass.parent.parent is None
                and project.projectClass.parent is not None
                else project.projectClass.parent.parent
                if project.projectClass.parent.parent is not None
                and project.projectClass.parent is not None
                else None
            )
            if project.projectClass is not None
            else None
        )
        projectRelations["planning"]["class"] = (
            (
                project.projectClass
                if project.projectClass.parent is not None
                and project.projectClass.parent.parent is None
                else project.projectClass.parent
                if project.projectClass.parent is not None
                and project.projectClass.parent.parent is not None
                else None
            )
            if project.projectClass is not None
            else None
        )
        projectRelations["planning"]["subClass"] = (
            (
                project.projectClass
                if project.projectClass.parent is not None
                and project.projectClass.parent.parent is not None
                else None
            )
            if project.projectClass is not None
            else None
        )
        projectRelations["planning"]["district"] = (
            (
                project.projectLocation
                if project.projectLocation.parent is None
                else project.projectLocation.parent
                if project.projectLocation.parent.parent is None
                and project.projectLocation.parent is not None
                else project.projectLocation.parent.parent
                if project.projectLocation.parent.parent is not None
                and project.projectLocation.parent is not None
                else None
            )
            if project.projectLocation is not None
            else None
        )

        projectRelations["planning"]["group"] = (
            project.projectGroup if project.projectGroup is not None else None
        )
        if projectRelations["planning"]["district"]:
            projectRelations["coordination"]["district"] = (
                projectRelations["planning"]["district"].coordinatorLocation
                if hasattr(
                    projectRelations["planning"]["district"], "coordinatorLocation"
                )
                else None
            )

        lowestLevelCoordinationClass = (
            projectRelations["planning"]["subClass"].coordinatorClass
            if projectRelations["planning"]["subClass"] != None
            and hasattr(projectRelations["planning"]["subClass"], "coordinatorClass")
            else projectRelations["planning"]["class"].coordinatorClass
            if projectRelations["planning"]["class"] != None
            and hasattr(projectRelations["planning"]["class"], "coordinatorClass")
            else projectRelations["planning"]["masterClass"].coordinatorClass
            if projectRelations["planning"]["masterClass"] != None
            and hasattr(projectRelations["planning"]["masterClass"], "coordinatorClass")
            else None
        )
        while lowestLevelCoordinationClass != None:
            classType = ProjectClassService.identify_class_type(
                classInstance=lowestLevelCoordinationClass
            )
            if classType != None:
                projectRelations["coordination"][
                    classType
                ] = lowestLevelCoordinationClass
            lowestLevelCoordinationClass = lowestLevelCoordinationClass.parent

        return projectRelations
