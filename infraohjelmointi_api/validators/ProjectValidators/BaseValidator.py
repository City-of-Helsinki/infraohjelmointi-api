from uuid import UUID
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist

from infraohjelmointi_api.models import Project


class BaseValidator:
    def getProjectInstance(self, id: UUID, serializer) -> Project | None:
        """
        Returns the correct Project Instance to the validator.
        Filters the project from queryset incase multiple projects are given.
        """
        if isinstance(serializer.instance, QuerySet):
            try:
                return serializer.instance.get(id=id)
            except ObjectDoesNotExist:
                return None

        return serializer.instance
