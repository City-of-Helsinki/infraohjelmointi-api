from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from infraohjelmointi_api.models import ProjectHashTag


class HashtagNameValidator:
    """
    Validator for checking if project already exists to a group
    """

    def __call__(self, hashtagName) -> None:
        if (
            hashtagName != None
            and ProjectHashTag.objects.filter(value=hashtagName).exists()
        ):
            raise ValidationError(
                detail="Hashtag already exists with the same name",
                code="hashtagUnique",
            )
