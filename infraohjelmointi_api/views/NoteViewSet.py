from .BaseViewSet import BaseViewSet
from infraohjelmointi_api.models import Note, NoteImage
from infraohjelmointi_api.serializers import (
    NoteGetSerializer,
    NoteImageSerializer,
    NoteUpdateSerializer,
    NoteCreateSerializer,
    NoteHistorySerializer,
)
from infraohjelmointi_api.utils.note_image_validation import validate_note_image
from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from overrides import override
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
import uuid
from rest_framework.response import Response
from rest_framework import status


class NoteViewSet(BaseViewSet):

    """
    API endpoint that allows notes to be viewed or edited.
    """

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

    @override
    def get_queryset(self):
        # IO-812: every Note response embeds images[]. Without prefetch this is
        # a classic N+1 on GET /notes/ (one extra query per row). The same
        # prefetch helps retrieve / create / update too.
        return Note.objects.prefetch_related("images")

    @action(methods=["get"], detail=True, url_path=r"history", name="get_note_history")
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

    @action(
        methods=["get", "post"],
        detail=True,
        url_path=r"images",
        name="note_images",
        parser_classes=[MultiPartParser, FormParser],
    )
    def images(self, request, pk):
        """List or upload images for a note (IO-812).

        GET  /notes/<noteId>/images/        -> NoteImage[]
        POST /notes/<noteId>/images/        -> NoteImage[]  (multipart, field 'file' x N)
        """
        note = self.get_object()
        if request.method == "GET":
            return Response(
                NoteImageSerializer(
                    note.images.all(), many=True, context={"request": request}
                ).data
            )

        files = request.FILES.getlist("file")
        if not files:
            raise ValidationError({"file": "At least one file is required."})

        # Validate everything up-front so a bad file in the middle of a batch
        # rejects the whole request before any row or blob is written.
        for f in files:
            validate_note_image(f)

        uploader = request.user if request.user.is_authenticated else None
        with transaction.atomic():
            # Re-aggregate inside the transaction so concurrent uploads to the
            # same note don't both pick the same base_order. Race is still
            # possible without a row lock, but the window is tiny and the only
            # consequence is two images sharing an order value (the carousel
            # tiebreaks on createdDate).
            base_order = (
                note.images.aggregate(Max("order"))["order__max"] or -1
            ) + 1
            created = [
                NoteImage.objects.create(
                    note=note,
                    file=f,
                    fileName=f.name,
                    contentType=(f.content_type or "").lower(),
                    size=f.size or 0,
                    order=base_order + i,
                    uploadedBy=uploader,
                )
                for i, f in enumerate(files)
            ]
        return Response(
            NoteImageSerializer(
                created, many=True, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        methods=["delete"],
        detail=True,
        url_path=r"images/(?P<imageId>[-\w]+)",
        name="delete_note_image",
    )
    def delete_image(self, request, pk, imageId):
        """Hard-delete a single note image (IO-812).

        DELETE /notes/<noteId>/images/<imageId>/  -> 204
        """
        try:
            uuid.UUID(str(imageId))
        except ValueError:
            return Response(
                data={"message": "Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
            )
        note = self.get_object()
        img = get_object_or_404(NoteImage, pk=imageId, note=note)
        # Remove the underlying blob/file before the row, so a failed delete
        # doesn't leave orphaned bytes referenced by a stale row.
        img.file.delete(save=False)
        img.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["get"],
        detail=True,
        url_path=r"history/(?P<userId>[-\w]+)",
        name="get_note_history_by_user",
    )
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
