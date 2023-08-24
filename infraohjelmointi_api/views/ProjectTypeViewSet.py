from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectTypeSerializer import ProjectTypeSerializer


class ProjectTypeViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectTypeSerializer
