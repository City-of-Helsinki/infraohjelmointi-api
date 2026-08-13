from rest_framework import serializers
from rest_framework.reverse import reverse

from infraohjelmointi_api.models import ConstructionHandoverAttachment


class ConstructionHandoverAttachmentSerializer(serializers.ModelSerializer):
    """Read-only representation of a handover attachment row (IO-857).

    Writes go through the @action endpoints on ConstructionHandoverViewSet, not this
    serializer.

    `downloadUrl` points at our own permission-checked download endpoint rather than
    exposing the raw storage URL. That keeps the container private and means the URL
    stays stable if we later switch to short-lived SAS links (the pattern the
    haitaton project uses) - the UI would not need to change.
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
        request = self.context.get("request") if self.context else None
        # Router basename is "constructionHandovers" (see project/urls.py), so the
        # reverse name is that plus the action's url_name.
        return reverse(
            "constructionHandovers-download-attachment",
            kwargs={"pk": str(obj.handover_id), "attachmentId": str(obj.id)},
            request=request,
        )
