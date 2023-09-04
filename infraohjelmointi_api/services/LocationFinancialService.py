from .ProjectClassService import ProjectClassService
from ..models import LocationFinancial, ProjectLocation


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
    def get_coordinator_location_and_related_location(
        instance: LocationFinancial,
    ) -> dict:
        """
        Returns the location instances for coordinator location linked to the LocationFinancial object and the related planning location linked to the coordinator Location.

            Parameters
            ----------
            instance : LocationFinancial
                instance of LocationFinancial to get relations

            Returns
            -------
            dict
                {
                "coordination": {
                    "<type_of_location>": <ProjectLocation instance>,
                    },
                "planning": {
                    "<type_of_location>": <ProjectLocation instance>,
                    },
                }
        """
        locationInstances = {"coordination": {}, "planning": {}}

        coordinatorLocationInstance: ProjectLocation = instance.locationRelation

        locationInstances["coordination"][
            ProjectClassService.identify_class_type(
                classInstance=coordinatorLocationInstance
            )
        ] = coordinatorLocationInstance

        locationInstances["planning"][
            ProjectClassService.identify_class_type(
                classInstance=coordinatorLocationInstance.relatedTo
            )
        ] = coordinatorLocationInstance.relatedTo

        # Traverse backwards from current Coordination location to get parent locations
        # Get related planning locations along the way
        currCoordinationLocation = coordinatorLocationInstance.parent
        while currCoordinationLocation != None:
            locationInstances["coordination"][
                ProjectClassService.identify_class_type(
                    classInstance=currCoordinationLocation
                )
            ] = currCoordinationLocation

            locationInstances["planning"][
                ProjectClassService.identify_class_type(
                    classInstance=currCoordinationLocation.relatedTo
                )
            ] = currCoordinationLocation.relatedTo

            currCoordinationLocation = currCoordinationLocation.parent

        return locationInstances
