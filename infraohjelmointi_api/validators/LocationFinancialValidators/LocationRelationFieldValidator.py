from rest_framework.exceptions import ValidationError
from infraohjelmointi_api.models import ProjectLocation


class LocationRelationFieldValidator:
    """
    Validator for checking if locationRelation field is a coordinator location
    """

    requires_context = False

    def __call__(self, locationRelation: ProjectLocation) -> None:
        if locationRelation.forCoordinatorOnly != True:
            raise ValidationError(
                detail="locationRelation field on a LocationFinancial instance must be a coordinator location",
                code="location_relation_not_coordinator",
            )
