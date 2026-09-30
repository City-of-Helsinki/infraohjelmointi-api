from rest_framework import serializers
from rest_framework.reverse import reverse

from infraohjelmointi_api.models import ConstructionHandoverAttachment


class ConstructionHandoverAttachmentSerializer(serializers.ModelSerializer):
    """Read-only representation of a handover attachment row (IO-857).

    Writes go through the @action endpoints on ConstructionHandoverViewSet, not this
    serializer.

    `downloadUrl` points at our own permission-checked download endpoint, never at
    storage (see utils/stored_files.py). It is a relative path, like
    NoteImageSerializer.url: the UI resolves it against its API base URL, and an
    absolute URL would come out as http:// behind Platta's TLS-terminating route.
    """

    downloadUrl = serializers.SerializerMethodField()

    class Meta:
        model = ConstructionHandoverAttachment
        fields = [
            "id",
            "handover",
            "downloadUrl",
            "originalName",
            "contentType",
            "size",
            "uploadedDate",
        ]
        read_only_fields = fields

    def get_downloadUrl(self, obj):
        if not obj.file:
            return None
        # Router basename is "constructionHandovers" (see project/urls.py), so the
        # reverse name is that plus the action's url_name.
        return reverse(
            "constructionHandovers-download-attachment",
            kwargs={"pk": str(obj.handover_id), "attachment_id": str(obj.id)},
        )
