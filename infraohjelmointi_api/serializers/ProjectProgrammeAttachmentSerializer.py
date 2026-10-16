from rest_framework import serializers
from rest_framework.reverse import reverse

from infraohjelmointi_api.models import ProjectProgrammeAttachment, ProjectProgrammeLocationMap


class ProjectProgrammeAttachmentSerializer(serializers.ModelSerializer):
    """Read-only representation of a section attachment row (IO-914).

    Writes go through the @action endpoints on ProjectProgrammeViewSet. Same shape as
    ConstructionHandoverAttachmentSerializer, so the UI can share its file list.

    `downloadUrl` is a relative path to our own permission-checked endpoint (see
    utils/stored_files.py). It is nested under the programme, whose id comes from
    context["programme_id"]: callers always know it, and resolving it from the
    generic FK would cost a query per row.
    """

    downloadUrl = serializers.SerializerMethodField()

    class Meta:
        model = ProjectProgrammeAttachment
        fields = [
            "id",
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
        return reverse(
            "projectProgrammes-download-section-attachment",
            kwargs={"pk": str(self.context["programme_id"]), "attachment_id": str(obj.id)},
        )


def get_section_attachments(section):
    """Serialize a section's attachments; uses the prefetch cache when present."""
    return ProjectProgrammeAttachmentSerializer(
        section.attachments.all(),
        many=True,
        context={"programme_id": section.project_programme_id},
    ).data


class ProjectProgrammeLocationMapSerializer(serializers.ModelSerializer):
    """Read-only representation of a programme's location map (IO-936).

    `url` serves the image itself, through the same permission-checked endpoint that
    handles POST/DELETE.
    """

    url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectProgrammeLocationMap
        fields = [
            "id",
            "url",
            "originalName",
            "contentType",
            "size",
            "uploadedDate",
        ]
        read_only_fields = fields

    def get_url(self, obj):
        if not obj.file:
            return None
        return reverse(
            "projectProgrammes-location-map",
            kwargs={"pk": str(obj.project_programme_id)},
        )
