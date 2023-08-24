from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectAreaSerializer import ProjectAreaSerializer


class ProjectAreaViewSet(BaseViewSet):
    """
    API endpoint that allows project areas to be viewed or edited.
    """

    permission_classes = []
    serializer_class = ProjectAreaSerializer
