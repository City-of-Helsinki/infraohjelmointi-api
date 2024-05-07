from .BaseViewSet import BaseViewSet
import logging
from infraohjelmointi_api.serializers.ProjectTypeSerializer import ProjectTypeSerializer

logger = logging.getLogger("infraohjelmointi_api")

class ProjectTypeViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """

    serializer_class = ProjectTypeSerializer
