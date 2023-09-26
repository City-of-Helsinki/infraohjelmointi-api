from .BaseViewSet import BaseViewSet

from infraohjelmointi_api.serializers.ProjectResponsibleZoneSerializer import (
    ProjectResponsibleZoneSerializer,
)


class ProjectResponsibleZoneViewSet(BaseViewSet):
    """
    API endpoint that allows Planning responsible zones to be viewed or edited.
    """

    serializer_class = ProjectResponsibleZoneSerializer
