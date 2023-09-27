from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectPrioritySerializer import (
    ProjectPrioritySerializer,
)
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page


class ProjectPriorityViewSet(BaseViewSet):
    """
    API endpoint that allows project Priority to be viewed or edited.
    """

    serializer_class = ProjectPrioritySerializer

    @method_decorator(cache_page(60 * 60 * 24))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
