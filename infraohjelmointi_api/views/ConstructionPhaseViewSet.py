from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ConstructionPhaseSerializer import (
    ConstructionPhaseSerializer,
)


class ConstructionPhaseViewSet(BaseViewSet):
    """
    API endpoint that allows Construction phases to be viewed or edited.
    """

    serializer_class = ConstructionPhaseSerializer
