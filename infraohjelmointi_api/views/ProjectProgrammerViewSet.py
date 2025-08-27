from rest_framework.viewsets import ReadOnlyModelViewSet
from infraohjelmointi_api.serializers.ProjectProgrammerSerializer import ProjectProgrammerSerializer
from infraohjelmointi_api.models import ProjectProgrammer


class ProjectProgrammerViewSet(ReadOnlyModelViewSet):
    """
    API endpoint that allows Project Programmers to be viewed.
    Read-only - programmers are managed through admin interface.
    """
    queryset = ProjectProgrammer.objects.all()
    serializer_class = ProjectProgrammerSerializer
