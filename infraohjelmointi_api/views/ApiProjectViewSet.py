from .BaseViewSet import BaseViewSet
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from infraohjelmointi_api.models import Project
from infraohjelmointi_api.serializers import ProjectGetSerializer

class ApiProjectViewSet(BaseViewSet):
    """
    API Project root. This endpoint is disabled.
    """

    http_method_names = ['get']

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Project.objects.all()
    serializer_class = ProjectGetSerializer

    def retrieve(self, request, pk=None):
        print(request)
        queryset = self.get_queryset()
        obj = queryset.get(pk=pk)
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
