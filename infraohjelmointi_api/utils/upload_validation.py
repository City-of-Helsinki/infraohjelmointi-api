"""Shared validation for user-uploaded files.

Introduced for IO-812 (note images) and reused by IO-857 (construction handover
attachments). IO-914 will want the same for hankeohjelma attachments, so the rules
are parameterised by (allowed content types, max bytes) rather than hard-wired to
one feature.

The exceptions surface as drf-standardized-errors responses, so the UI can branch on
stable string codes ("unsupported_media_type", "payload_too_large") instead of
parsing prose.
"""

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException


class UnsupportedUploadType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = "Tiedostotyyppi ei ole sallittu."
    default_code = "unsupported_media_type"


class UploadTooLarge(APIException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "Tiedosto on liian suuri."
    default_code = "payload_too_large"


def _describe_types(allowed_types) -> str:
    """Render MIME types the way the UI shows them ("jpg, png")."""
    return ", ".join(t.rsplit("/", 1)[-1] for t in allowed_types)


def validate_upload(uploaded_file, allowed_types, max_bytes) -> None:
    """Raise APIException if the uploaded file violates the given constraints."""
    content_type = (uploaded_file.content_type or "").lower()
    if content_type not in allowed_types:
        raise UnsupportedUploadType(
            detail=(
                f"Tiedostotyyppi '{content_type or 'tuntematon'}' ei ole sallittu. "
                f"Sallitut tiedostotyypit: {_describe_types(allowed_types)}."
            )
        )

    # size is None for some exotic upload handlers; treat unknown size as acceptable
    # here rather than rejecting, since the web server body limit is the real backstop.
    if uploaded_file.size is not None and uploaded_file.size > max_bytes:
        raise UploadTooLarge(
            detail=(
                f"Tiedosto on liian suuri ({uploaded_file.size} tavua). "
                f"Maksimikoko on {max_bytes} tavua."
            )
        )


def validate_note_image(uploaded_file) -> None:
    """IO-812: validate a note image upload."""
    validate_upload(
        uploaded_file,
        settings.NOTE_IMAGE_ALLOWED_TYPES,
        settings.NOTE_IMAGE_MAX_BYTES,
    )


def validate_handover_attachment(uploaded_file) -> None:
    """IO-857: validate a construction handover attachment upload."""
    validate_upload(
        uploaded_file,
        settings.HANDOVER_ATTACHMENT_ALLOWED_TYPES,
        settings.HANDOVER_ATTACHMENT_MAX_BYTES,
    )
