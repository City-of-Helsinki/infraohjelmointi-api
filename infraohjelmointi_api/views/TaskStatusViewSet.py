from infraohjelmointi_api.serializers.TaskStatusSerializer import TaskStatusSerializer

from .CachedLookupViewSet import CachedLookupViewSet


class TaskStatusViewSet(CachedLookupViewSet):
    """API endpoint for task statuses (cached)."""

    serializer_class = TaskStatusSerializer
