from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.TaskSerializer import TaskSerializer


class TaskViewSet(BaseViewSet):
    """
    API endpoint that allows Tasks to be viewed or edited.
    """

    serializer_class = TaskSerializer
