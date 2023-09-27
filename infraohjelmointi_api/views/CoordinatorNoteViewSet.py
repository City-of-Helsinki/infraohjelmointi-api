from django.shortcuts import get_object_or_404

from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.CoordinatorNoteSerializer import CoordinatorNoteSerializer

class CoordinatorNoteViewSet(BaseViewSet):
    """
    API endpoint that allows coordinator notes to be viewed and added.
    """

    serializer_class = CoordinatorNoteSerializer
