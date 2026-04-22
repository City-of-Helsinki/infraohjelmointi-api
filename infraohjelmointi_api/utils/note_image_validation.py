"""Validation helpers for IO-812 note image uploads.

Phase 1 only enforces content-type and byte size limits sourced from settings.
The exceptions raised here surface as drf-standardized-errors responses so the
UI can branch on stable string codes ("unsupported_media_type",
"payload_too_large") rather than parsing prose.
"""

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException


class UnsupportedNoteImageType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = "Vain jpg ja png tiedostot ovat sallittuja."
    default_code = "unsupported_media_type"


class NoteImageTooLarge(APIException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = "Tiedosto on liian suuri."
    default_code = "payload_too_large"


def validate_note_image(uploaded_file) -> None:
    """Raise APIException if the uploaded file violates note-image rules."""
    content_type = (uploaded_file.content_type or "").lower()
    if content_type not in settings.NOTE_IMAGE_ALLOWED_TYPES:
        raise UnsupportedNoteImageType(
            detail=(
                f"Tiedostotyyppi '{content_type or 'unknown'}' ei ole sallittu. "
                f"Sallitut tyypit: {', '.join(settings.NOTE_IMAGE_ALLOWED_TYPES)}."
            )
        )

    max_bytes = settings.NOTE_IMAGE_MAX_BYTES
    if uploaded_file.size is not None and uploaded_file.size > max_bytes:
        raise NoteImageTooLarge(
            detail=(
                f"Tiedosto on liian suuri ({uploaded_file.size} tavua). "
                f"Maksimikoko on {max_bytes} tavua."
            )
        )
