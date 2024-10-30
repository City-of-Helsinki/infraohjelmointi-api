from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.AppStateValueSerializer import AppStateValueSerializer
from rest_framework.decorators import action

class AppStateValueViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """

    serializer_class = AppStateValueSerializer