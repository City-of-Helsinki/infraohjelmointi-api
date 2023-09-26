from rest_framework.exceptions import ValidationError
from infraohjelmointi_api.models import ProjectClass


class ClassRelationFieldValidator:
    """
    Validator for checking if classRelation field is a coordinator class
    """

    requires_context = False

    def __call__(self, classRelation: ProjectClass) -> None:
        if classRelation.forCoordinatorOnly != True:
            raise ValidationError(
                detail="classRelation field on a ClassFinancial instance must be a coordinator class",
                code="class_relation_not_coordinator",
            )
