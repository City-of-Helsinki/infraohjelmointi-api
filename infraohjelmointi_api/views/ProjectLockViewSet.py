from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ProjectLockSerializer import ProjectLockSerializer


class ProjectLockViewSet(BaseViewSet):
    """
    API endpoint that allows Project Lock status to be viewed or edited.
    """

    serializer_class = ProjectLockSerializer
