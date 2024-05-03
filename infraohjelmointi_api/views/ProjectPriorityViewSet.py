from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectPrioritySerializer import (
    ProjectPrioritySerializer,
)


class ProjectPriorityViewSet(BaseViewSet):
    """
    API endpoint that allows project Priority to be viewed or edited.
    """

    serializer_class = ProjectPrioritySerializer
