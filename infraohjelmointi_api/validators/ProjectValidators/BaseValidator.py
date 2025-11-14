from uuid import UUID
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist

from infraohjelmointi_api.models import Project


class BaseValidator:
    def getProjectInstance(self, id: UUID, serializer) -> Project | None:
        """
        Returns the correct Project Instance to the validator.
        Filters the project from queryset incase multiple projects are given.
        Handles three scenarios:
        1. QuerySet: Get project by ID from queryset
        2. List: Find project by ID from list (bulk update with many=True)
        3. Single instance: Return the instance directly
        """
        if isinstance(serializer.instance, QuerySet):
            try:
                return serializer.instance.get(id=id)
            except ObjectDoesNotExist:
                return None
        
        # Handle list of instances (bulk update scenario with many=True)
        # When many=True, DRF passes a list of instances to the serializer
        if isinstance(serializer.instance, list):
            try:
                return next(project for project in serializer.instance if project.id == id)
            except (StopIteration, AttributeError):
                # StopIteration: No project found with matching ID
                # AttributeError: Item in list doesn't have .id attribute
                return None

        return serializer.instance
