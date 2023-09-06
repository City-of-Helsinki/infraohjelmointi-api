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
