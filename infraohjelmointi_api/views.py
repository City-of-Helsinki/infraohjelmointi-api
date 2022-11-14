from rest_framework import viewsets
from .serializers import ProjectSerializer, ProjectTypeSerializer


class BaseViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.all()


class ProjectViewSet(BaseViewSet):
    """
    API endpoint that allows projects to be viewed or edited.
    """
    permission_classes = []
    serializer_class = ProjectSerializer


class ProjectTypeViewSet(BaseViewSet):
    """
    API endpoint that allows project types to be viewed or edited.
    """
    permission_classes = []
    serializer_class = ProjectTypeSerializer
