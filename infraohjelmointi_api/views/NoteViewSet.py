from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.serializers import (
    NoteGetSerializer,
    NoteUpdateSerializer,
    NoteCreateSerializer,
    NoteHistorySerializer,
)
from overrides import override
from rest_framework.decorators import action
import uuid
from rest_framework.response import Response
from rest_framework import status


class NoteViewSet(BaseViewSet):

    """
    API endpoint that allows notes to be viewed or edited.
    """

    permission_classes = []

    @override
    def get_serializer_class(self):
        """
        Overriden ModelViewSet class method to get appropriate serializer depending on the request action
        """
        if self.action in ["list", "retrieve"]:
            return NoteGetSerializer
        if self.action == "create":
            return NoteCreateSerializer
        return NoteUpdateSerializer

    @action(methods=["get"], detail=True, url_path=r"history")
    def history(self, request, pk):
        """
        Custom action to get edit history of a note

            URL Parameters
            ----------

            note_id : UUID string

            Usage
            ----------

            notes/<note_id>/history/

            Returns
            -------

            JSON
                List of ProjectNote instances
        """
        try:
            uuid.UUID(str(pk))  # validating UUID
            instance = self.get_object()
            qs = instance.history.all()
            serializer = NoteHistorySerializer(qs, many=True)
            return Response(serializer.data)
        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )

    @override
    def destroy(self, request, *args, **kwargs):
        """
        Overriding destroy action to soft delete note on DELETE request
        """
        note = self.get_object()
        data = note.id
        note.deleted = True
        note.save()
        return Response({"id": data})

    @action(methods=["get"], detail=True, url_path=r"history/(?P<userId>[-\w]+)")
    def history_user(self, request, pk, userId):
        """
        Custom action to get edit history of a note edited by a specific user
            URL Parameters
            ----------

            note_id : UUID string

            user_id : UUID string

            Usage
            ----------

            notes/<note_id>/history/<user_id>/

            Returns
            -------

            JSON
                List of ProjectNote instances
        """
        try:
            uuid.UUID(str(userId))
            uuid.UUID(str(pk))
            instance = self.get_object()
            qs = instance.history.all().filter(updatedBy_id=userId)
            serializer = NoteHistorySerializer(qs, many=True)
            return Response(serializer.data)

        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )
