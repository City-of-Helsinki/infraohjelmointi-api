from django.urls import reverse
from rest_framework import serializers

from infraohjelmointi_api.models import NoteImage


class NoteImageSerializer(serializers.ModelSerializer):
    """Read-only representation of a NoteImage row.

    Writes go through the @action endpoints on NoteViewSet, not this serializer.

    `url` points at the API's own download endpoint, never at storage. With Azure
    Blob the storage URL would carry the container-wide SAS token (django-storages
    appends the client credential when no per-blob SAS can be signed), handing a
    long-lived read/write credential to every client. Serving through the API keeps
    the token server-side and applies note permissions to every download.

    The path is relative on purpose: the UI resolves it against its API base URL,
    and build_absolute_uri would yield http:// behind Platta's TLS-terminating
    route (no SECURE_PROXY_SSL_HEADER), which an https UI blocks as mixed content.
    """

    url = serializers.SerializerMethodField()

    class Meta:
        model = NoteImage
        fields = [
            "id",
            "url",
            "fileName",
            "contentType",
            "size",
            "order",
            "createdDate",
        ]
        read_only_fields = fields

    def get_url(self, obj):
        if not obj.file:
            return None
        return reverse(
            "notes-image-file", kwargs={"pk": obj.note_id, "image_id": obj.id}
        )
