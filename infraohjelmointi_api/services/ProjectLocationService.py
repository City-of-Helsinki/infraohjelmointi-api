from ..models import ProjectClass, ProjectLocation
from .ProjectClassService import ProjectClassService


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
        return (
            ProjectLocation.objects.all()
            .filter(forCoordinatorOnly=False)
            .order_by("createdDate")
        )

    @staticmethod
    def list_all_for_coordinator() -> list[ProjectLocation]:
        """List all project locations for coordinator view"""
        return (
            ProjectLocation.objects.all()
            .filter(forCoordinatorOnly=True)
            .order_by("createdDate")
        )

    @staticmethod
    def find_by_path(path: str) -> list[ProjectLocation]:
        """Find all project locations by path for programmer view"""
        return list(
            ProjectLocation.objects.all().filter(path=path, forCoordinatorOnly=False)
        )

    @staticmethod
    def get_by_id(id: str) -> ProjectLocation:
        """Get project location by id"""
        return ProjectLocation.objects.get(id=id)

    @staticmethod
    def instance_exists(id: str, forCoordinatorOnly: bool = False) -> bool:
        """Check if instance exists in DB"""
        return ProjectLocation.objects.filter(
            id=id, forCoordinatorOnly=forCoordinatorOnly
        ).exists()

    @staticmethod
    def identify_location_type(locationInstance: ProjectLocation) -> str:
        """
        Returns the type of location instance provided.

            Parameters
            ----------
            locationInstance : ProjectLocation
                Location instance used to identify type

            Returns
            -------
            str
                Type of location instance. Types: [district | division | subDivision | subLevelDistrict]
        """
        if (
            locationInstance != None
            and locationInstance.parent == None
            and locationInstance.forCoordinatorOnly == False
        ) or (
            locationInstance != None
            and locationInstance.parent == None
            and locationInstance.forCoordinatorOnly == True
            and ProjectClassService.identify_class_type(locationInstance.parentClass)
            != "collectiveSubLevel"
        ):
            return "district"

        if (
            locationInstance != None
            and locationInstance.parent == None
            and locationInstance.forCoordinatorOnly == True
            and ProjectClassService.identify_class_type(locationInstance.parentClass)
            == "collectiveSubLevel"
        ):
            return "subLevelDistrict"

        if (
            locationInstance != None
            and locationInstance.parent != None
            and locationInstance.parent.parent == None
        ):
            return "division"

        if (
            locationInstance != None
            and locationInstance.parent != None
            and locationInstance.parent.parent != None
            and locationInstance.parent.parent.parent == None
        ):
            return "subDivision"

        return None

    @staticmethod
    def list_all_locations() -> list[ProjectLocation]:
        """List all project locations"""
        return (
            ProjectLocation.objects.all()
            .order_by("createdDate")
        )