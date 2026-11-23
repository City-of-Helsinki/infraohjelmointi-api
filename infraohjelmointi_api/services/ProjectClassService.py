from ..models import ProjectClass, ProjectLocation


class ProjectClassService:
    @staticmethod
    def is_project_area_planner(user) -> bool:
        planner_flag = getattr(user, "is_project_area_planner", None)
        if planner_flag is True or planner_flag is False:
            return planner_flag

        group_names = getattr(user, "_cached_group_names", None)
        if group_names is None and hasattr(user, "groups"):
            group_names = set(user.groups.values_list("name", flat=True))
            setattr(user, "_cached_group_names", group_names)

        is_planner = bool(group_names and "project_area_planners" in group_names)
        setattr(user, "is_project_area_planner", is_planner)
        return is_planner

    @staticmethod
    def get_or_create(
        name: str,
        parent: ProjectClass | None,
        path: str,
        forCoordinatorOnly: bool = False,
        relatedTo: ProjectClass = None,
        relatedLocation: ProjectLocation = None,
    ) -> ProjectClass:
        return ProjectClass.objects.get_or_create(
            name=name,
            parent=parent,
            path=path,
            forCoordinatorOnly=forCoordinatorOnly,
            relatedTo=relatedTo,
            relatedLocation=relatedLocation,
        )

    @staticmethod
    def list_all() -> list[ProjectClass]:
        """List all project classes for programmer view"""
        return (
            ProjectClass.objects.all()
            .filter(forCoordinatorOnly=False)
            .order_by("createdDate")
        )

    @staticmethod
    def list_all_for_coordinator() -> list[ProjectClass]:
        """List all project classes for coordinator view"""
        return (
            ProjectClass.objects.all()
            .filter(forCoordinatorOnly=True)
            .order_by("createdDate")
        )

    @staticmethod
    def list_all_classes() -> list[ProjectClass]:
        """List all both coordinator and programmer view classes"""
        return (
            ProjectClass.objects.all().order_by("createdDate")
        )

    @staticmethod
    def get_by_id(id: str) -> ProjectClass:
        """Get project class by id"""
        return ProjectClass.objects.get(id=id)

    @staticmethod
    def instance_exists(id: str, forCoordinatorOnly: bool = False) -> ProjectClass:
        """Check if instance exists in DB"""
        return ProjectClass.objects.filter(
            id=id, forCoordinatorOnly=forCoordinatorOnly
        ).exists()

    @staticmethod
    def identify_class_type(classInstance: ProjectClass) -> str:
        """
        Returns the type of class instance provided.

            Parameters
            ----------
            classInstance : ProjectClass
                Class instance used to identify type

            Returns
            -------
            str
                Type of class instance. Types: [masterClass | class | subClass | collectiveSubLevel | otherClassification]
        """
        if classInstance != None and classInstance.parent == None:
            return "masterClass"

        if (
            classInstance != None
            and classInstance.parent != None
            and classInstance.parent.parent == None
        ):
            return "class"

        if (
            classInstance != None
            and classInstance.parent != None
            and classInstance.parent.parent != None
            and classInstance.parent.parent.parent == None
        ):
            return "subClass"

        if (
            classInstance != None
            and classInstance.parent != None
            and classInstance.parent.parent != None
            and classInstance.parent.parent.parent != None
            and classInstance.parent.parent.parent.parent == None
        ):
            return "collectiveSubLevel"

        if (
            classInstance != None
            and classInstance.parent != None
            and classInstance.parent.parent != None
            and classInstance.parent.parent.parent != None
            and classInstance.parent.parent.parent.parent != None
            and classInstance.parent.parent.parent.parent.parent == None
        ):
            return "otherClassification"
        return None
