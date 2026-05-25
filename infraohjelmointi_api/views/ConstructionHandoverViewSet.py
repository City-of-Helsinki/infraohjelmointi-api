from overrides import override
from rest_framework.response import Response
from rest_framework import status

from infraohjelmointi_api.models import ConstructionHandover

from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers import (
    ConstructionHandoverGetSerializer,
    ConstructionHandoverCreateSerializer,
    ConstructionHandoverUpdateSerializer
)

class ConstructionHandoverViewSet(BaseViewSet):
    
    """
    API endpoint that allows construction handovers to be viewed or edited.
    """

    @override
    def get_serializer_class(self):
        """
        Overriden ModelViewSet class method to get appropriate serializer depending on the request action
        """
        if self.action in ["list", "retrieve"]:
            return ConstructionHandoverGetSerializer
        elif self.action == "create":
            return ConstructionHandoverCreateSerializer
        return ConstructionHandoverUpdateSerializer

    def _get_authenticated_user(self, request):
        user = getattr(request, "user", None)
        if user and getattr(user, "is_authenticated", False):
            return user
        return None

    @override
    def perform_create(self, serializer):
        user = self._get_authenticated_user(self.request)
        if user:
            serializer.save(createdBy=user, updatedBy=user)
            return
        serializer.save()

    @override
    def create(self, request, *args, **kwargs):  
        project_id = request.data.get("project")
        # Check if there's an active handover for the project
        # (excluding MOVED_TO_CONSTRUCTION_PREPARATION status)
        # before allowing creation of a new one
        if project_id and ConstructionHandover.objects.filter(  
            project_id=project_id,  
        ).exclude(status="MOVED_TO_CONSTRUCTION_PREPARATION").exists():  
            return Response(  
                {"detail": "An active construction handover already exists for this project."},  
                status=status.HTTP_409_CONFLICT,  
            )  
        return super().create(request, *args, **kwargs)  

    @override
    def perform_update(self, serializer):
        user = self._get_authenticated_user(self.request)
        if user:
            serializer.save(updatedBy=user)
            return
        serializer.save()
    
    @override
    def partial_update(self, request, *args, **kwargs):
        """
        Overriden ModelViewSet class method to prevent updates if the handover is locked (not in DRAFT status)
        """
        instance = self.get_object()
        if instance.is_locked:
            return Response(
                {"detail": "Only construction handovers in DRAFT status can be edited."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().partial_update(request, *args, **kwargs)
    
    @override
    def destroy(self, request, *args, **kwargs):
        """
        Overriden ModelViewSet class method to prevent deletion if the handover is not in DRAFT status
        """
        instance = self.get_object()
        if instance.is_locked:
            return Response(
                {"detail": "Only construction handovers in DRAFT status can be deleted."},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)