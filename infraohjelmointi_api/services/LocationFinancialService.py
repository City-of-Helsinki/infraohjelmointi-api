from .ProjectClassService import ProjectClassService
from ..models import LocationFinancial, ProjectClass


class LocationFinancialService:
    @staticmethod
    def get_or_create(year: str, location_id: str) -> LocationFinancial:
        return LocationFinancial.objects.get_or_create(
            year=year, locationRelation_id=location_id
        )

    @staticmethod
    def update_or_create(
        year: str, location_id: str, updatedData: dict
    ) -> LocationFinancial:
        return LocationFinancial.objects.update_or_create(
            year=year, locationRelation_id=location_id, defaults=updatedData
        )

    @staticmethod
    def get(location_id: str, year: str) -> LocationFinancial:
        return LocationFinancial.objects.get(locationRelation_id=location_id, year=year)

    @staticmethod
    def get_request_field_to_year_mapping(start_year: int):
        return {"year{}".format(index): start_year + index for index in range(0, 11)}

    @staticmethod
    def get_coordinator_class_and_related_class(instance: LocationFinancial) -> dict:
        """
        Returns the class instances for coordinator class linked to the LocationFinancial object and the related planning class linked to the coordinator Class.

            Parameters
            ----------
            instance : LocationFinancial
                instance of LocationFinancial to get relations

            Returns
            -------
            dict
                {
                "coordination": {
                    "<type_of_class>": <ProjectClass instance>,
                    },
                "planning": {
                    "<type_of_class>": <ProjectClass instance>,
                    },
                }
        """
        classInstances = {"coordination": {}, "planning": {}}

        coordinatorClassInstance: ProjectClass = instance.classRelation

        classInstances["coordination"][
            ProjectClassService.identify_class_type(
                classInstance=coordinatorClassInstance
            )
        ] = coordinatorClassInstance

        classInstances["planning"][
            ProjectClassService.identify_class_type(
                classInstance=coordinatorClassInstance.relatedTo
            )
        ] = coordinatorClassInstance.relatedTo

        # Traverse backwards from current Coordination Class to get parent classes
        # Get related planning classes along the way
        currCoordinationClass = coordinatorClassInstance.parent
        while currCoordinationClass != None:
            classInstances["coordination"][
                ProjectClassService.identify_class_type(
                    classInstance=currCoordinationClass
                )
            ] = currCoordinationClass

            classInstances["planning"][
                ProjectClassService.identify_class_type(
                    classInstance=currCoordinationClass.relatedTo
                )
            ] = currCoordinationClass.relatedTo

            currCoordinationClass = currCoordinationClass.parent

        return classInstances
