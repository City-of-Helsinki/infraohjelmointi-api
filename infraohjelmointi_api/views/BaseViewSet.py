from rest_framework import viewsets

from overrides import override
from helusers.oidc import ApiTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from ..permissions import *


class BaseViewSet(viewsets.ModelViewSet):
    #permissions can uncommented to test
    permission_classes = [
        IsAuthenticated
        & (
            IsCoordinator
            or IsPlanner
            or IsPlannerOfProjectAreas
            or IsProjectManager
            or IsViewer
            or IsAdmin
        )
    ]
    authentication_classes = [ApiTokenAuthentication, SessionAuthentication]

    @override
    def get_queryset(self):
        """
        Overriden ModelViewSet class method to get appropriate queryset using serializer class
        """
        return self.get_serializer_class().Meta.model.objects.all()
