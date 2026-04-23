from .CachedLookupViewSet import CachedLookupViewSet
from infraohjelmointi_api.serializers.PersonSerializer import PersonSerializer


class PersonViewSet(CachedLookupViewSet):
    """
    API endpoint that allows persons to be viewed or edited.
    """

    serializer_class = PersonSerializer
    preserved_fields = ['firstName', 'lastName', 'email', 'phone', 'title']
