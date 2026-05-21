from .CachedLookupViewSet import CachedLookupViewSet
from infraohjelmointi_api.serializers.PersonSerializer import PersonSerializer


class PersonViewSet(CachedLookupViewSet):
    """
    API endpoint that allows persons to be viewed or edited.
    """

    serializer_class = PersonSerializer
    preserved_fields = ['firstName', 'lastName', 'email', 'phone', 'title']
    # Person is referenced by Project via two FK fields. Both must be cleaned
    # up (or repointed to a hidden copy for completed/warranty projects) on
    # delete; otherwise Postgres rejects the delete with a FK violation.
    # M2M fields (otherPersons, favPersons) are auto-cleaned by Django.
    project_field = ('personPlanning', 'personConstruction')
