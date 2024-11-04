from .ProjectLocationService import ProjectLocationService
from .ProjectClassService import ProjectClassService
from ..models import LocationFinancial, ProjectLocation


class LocationFinancialService:
    @staticmethod
    def get_or_create(year: str, location_id: str, for_frame_view: bool) -> LocationFinancial:
        return LocationFinancial.objects.get_or_create(
            year=year, locationRelation_id=location_id, forFrameView=for_frame_view
        )

    @staticmethod
    def update_or_create(
        year: str, location_id: str, updatedData: dict, for_frame_view: bool
    ) -> LocationFinancial:
        return LocationFinancial.objects.update_or_create(
            year=year, locationRelation_id=location_id, forFrameView=for_frame_view, defaults=updatedData
        )

    @staticmethod
    def get(location_id: str, year: str, for_frame_view: bool) -> LocationFinancial:
        return LocationFinancial.objects.get(locationRelation_id=location_id, year=year, forFrameView=for_frame_view)

    @staticmethod
    def get_request_field_to_year_mapping(start_year: int):
        return {"year{}".format(index): start_year + index for index in range(0, 11)}

    @staticmethod
    def get_coordinator_location_and_related_classes(
        instance: LocationFinancial,
    ) -> dict:
        """
        Returns the location instances for coordinator/planning location linked to the LocationFinancial object and the related planning classes which are above the coordinator location.

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
                    "<type_of_class>": <ProjectClass instance>
                    },
                "planning": {
                    "<type_of_location>": <ProjectLocation instance>,
                    "<type_of_class>": <ProjectClass instance>
                    },
                }
        """
        locationFinancialRelations = {"coordination": {}, "planning": {}}

        coordinatorLocationInstance: ProjectLocation = instance.locationRelation

        locationFinancialRelations["coordination"][
            "district"
        ] = coordinatorLocationInstance

        locationFinancialRelations["planning"][
            "district"
        ] = coordinatorLocationInstance.relatedTo

        # Traverse backwards from current Coordination Location to get parent classes
        currCoordinationClass = coordinatorLocationInstance.parentClass
        while currCoordinationClass != None:
            locationFinancialRelations["coordination"][
                ProjectClassService.identify_class_type(
                    classInstance=currCoordinationClass
                )
            ] = currCoordinationClass

            locationFinancialRelations["planning"][
                ProjectClassService.identify_class_type(
                    classInstance=currCoordinationClass.relatedTo
                )
            ] = currCoordinationClass.relatedTo

            currCoordinationClass = currCoordinationClass.parent

        return locationFinancialRelations
