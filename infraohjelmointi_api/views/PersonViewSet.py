from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers.PersonSerializer import PersonSerializer


class PersonViewSet(BaseViewSet):
    """
    API endpoint that allows persons to be viewed or edited.
    """

    serializer_class = PersonSerializer
