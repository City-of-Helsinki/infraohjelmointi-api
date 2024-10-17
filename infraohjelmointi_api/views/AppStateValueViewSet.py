from infraohjelmointi_api.serializers.AppStateValueSerializer import AppStateValueSerializer
from .BaseViewSet import BaseViewSet


class AppStateValueViewSet(BaseViewSet):
    """
    API endpoint that allows values related to App state to be viewed or edited
    """

    serializer_class = AppStateValueSerializer