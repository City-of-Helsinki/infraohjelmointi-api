from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from infraohjelmointi_api.serialazers import ProjectSerializer, ProjectTypeSerializer


class ProjectViewSet(viewsets.ModelViewSet):
  """
  API endpoint that allows projects to be viewed or edited.
  """
  permission_classes = []

  queryset = User.objects.all()
  serializer_class = ProjectSerializer


class ProjectTypeViewSet(viewsets.ModelViewSet):
  """
  API endpoint that allows project types to be viewed or edited.
  """
  permission_classes = []

  queryset = Group.objects.all()
  serializer_class = ProjectTypeSerializer
