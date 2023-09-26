from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.ConstructionPhaseDetailSerializer import (
    ConstructionPhaseDetailSerializer,
)


class ConstructionPhaseDetailViewSet(BaseViewSet):
    """
    API endpoint that allows construction phase details to be viewed or edited.
    """

    serializer_class = ConstructionPhaseDetailSerializer
