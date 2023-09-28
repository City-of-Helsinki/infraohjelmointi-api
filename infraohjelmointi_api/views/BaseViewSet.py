from rest_framework import viewsets

from overrides import override
from helusers.oidc import ApiTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from ..permissions import IsCoordinator


class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated | (IsCoordinator)]
    authentication_classes = [ApiTokenAuthentication, SessionAuthentication]

    @override
    def get_queryset(self):
        """
        Overriden ModelViewSet class method to get appropriate queryset using serializer class
        """
        return self.get_serializer_class().Meta.model.objects.all()
