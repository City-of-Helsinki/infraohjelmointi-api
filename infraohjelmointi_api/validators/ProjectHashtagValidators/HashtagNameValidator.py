from rest_framework.exceptions import ValidationError
from infraohjelmointi_api.models import ProjectHashTag
from infraohjelmointi_api.services.ProjectHashTagService import ProjectHashTagService


class HashtagNameValidator:
    """
    Validator for checking if project already exists to a group
    """

    def __call__(self, hashtagName) -> None:
        if (
            hashtagName != None
            and ProjectHashTagService.find_by_name(name=hashtagName).exists()
        ):
            raise ValidationError(
                detail="Hashtag already exists with the same name",
                code="hashtagUnique",
            )
