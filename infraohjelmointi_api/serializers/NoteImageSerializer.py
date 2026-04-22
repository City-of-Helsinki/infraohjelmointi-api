from rest_framework import serializers

from infraohjelmointi_api.models import NoteImage


class NoteImageSerializer(serializers.ModelSerializer):
    """Read-only representation of a NoteImage row.

    Writes go through the @action endpoints on NoteViewSet, not this serializer.
    `url` is built absolute when a request is in the serializer context so the UI
    can render it directly without prefixing.
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
        request = self.context.get("request") if self.context else None
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url
