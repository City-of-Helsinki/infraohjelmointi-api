from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers import (
    ProjectSetGetSerializer,
    ProjectSetCreateSerializer,
)

from overrides import override


class ProjectSetViewSet(BaseViewSet):
    """
    API endpoint that allows project sets to be viewed or edited.
    """

    @override
    def get_queryset(self):
        """Optimize queryset with prefetch_related to prevent N+1 queries"""
        return (
            super()
            .get_queryset()
            .prefetch_related("project_set", "project_set__finances")
        )

    @override
    def get_serializer_class(self):
        """
        Overriden ModelViewSet class method to get appropriate serializer depending on the request action
        """
        if self.action == "list":
            return ProjectSetGetSerializer
        if self.action == "retrieve":
            return ProjectSetGetSerializer
        return ProjectSetCreateSerializer
