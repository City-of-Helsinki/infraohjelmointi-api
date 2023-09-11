from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.TaskStatusSerializer import TaskStatusSerializer


class TaskStatusViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """

    serializer_class = TaskStatusSerializer
