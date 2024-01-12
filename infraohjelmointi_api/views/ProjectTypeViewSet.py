from .BaseViewSet import BaseViewSet
import logging
from infraohjelmointi_api.serializers.ProjectTypeSerializer import ProjectTypeSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

logger = logging.getLogger("infraohjelmointi_api")

class ProjectTypeViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """

    serializer_class = ProjectTypeSerializer

    @method_decorator(cache_page(60 * 60 * 24))
    def list(self, request, *args, **kwargs):
        logger.info(super().list(request, *args, **kwargs))
        return super().list(request, *args, **kwargs)
