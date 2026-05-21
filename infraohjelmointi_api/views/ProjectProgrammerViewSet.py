from .CachedLookupViewSet import CachedLookupViewSet
from infraohjelmointi_api.serializers.ProjectProgrammerSerializer import ProjectProgrammerSerializer
from infraohjelmointi_api.models import ProjectProgrammer


class ProjectProgrammerViewSet(CachedLookupViewSet):
    """
    API endpoint that allows Project Programmers to be viewed or edited.
    """
    queryset = ProjectProgrammer.objects.all()
    serializer_class = ProjectProgrammerSerializer
    project_field = 'personProgramming'
    preserved_fields = ['firstName', 'lastName']
