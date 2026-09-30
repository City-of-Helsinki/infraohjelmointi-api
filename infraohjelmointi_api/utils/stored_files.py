"""Shared handling of user-uploaded files (IO-812, reused by IO-857).

Uploaded files are always streamed through the API, never linked to storage
directly: with Platta's SAS-only Azure auth, django-storages cannot sign
per-blob URLs, so a storage URL would carry the container-wide SAS token.
Serving through the API keeps the token server-side and applies the viewset's
permissions to every download.
"""

import logging
import os
from contextlib import contextmanager

from django.http import FileResponse, Http404

logger = logging.getLogger("infraohjelmointi_api")


def _missing_file_errors():
    # AzureStorage opens lazily and raises its own not-found error on first read;
    # the azure SDK is only importable when django-storages[azure] is installed.
    errors = [FileNotFoundError]
    try:
        from azure.core.exceptions import ResourceNotFoundError

        errors.append(ResourceNotFoundError)
    except ImportError:
        pass
    return tuple(errors)


MISSING_FILE_ERRORS = _missing_file_errors()


def stored_file_response(field_file, content_type, filename, as_attachment=False):
    """Stream a FieldFile back to the caller.

    Raises Http404 if the row exists but its bytes are missing from storage.
    """
    try:
        file_handle = field_file.open("rb")
        # Force the read here: AzureStorage defers the download until first
        # access, which would otherwise happen inside FileResponse and surface
        # a missing blob as a 500.
        file_handle.seek(0)
    except MISSING_FILE_ERRORS:
        raise Http404("File not found.")
    response = FileResponse(
        file_handle,
        content_type=content_type or "application/octet-stream",
        as_attachment=as_attachment,
        filename=filename,
    )
    # contentType comes from the client at upload time; nosniff stops a browser
    # from reinterpreting a mislabelled upload as HTML/script.
    response["X-Content-Type-Options"] = "nosniff"
    # The bytes never change for a given id, but they are user-scoped data, so
    # allow the browser's own cache only.
    response["Cache-Control"] = "private, max-age=3600"
    return response


def display_file_name(name, max_length=255):
    """Fit an uploaded file's original name into a CharField, keeping the extension."""
    if len(name) <= max_length:
        return name
    root, ext = os.path.splitext(name)
    ext = ext[: max_length // 2]
    return root[: max_length - len(ext)] + ext


@contextmanager
def cleanup_files_on_error(saved_rows):
    """Delete the stored files of rows created inside a block that then fails.

    Use outside transaction.atomic(): the rollback discards the rows, but each
    file was already written to storage when its row was saved.
    """
    try:
        yield
    except Exception:
        for row in saved_rows:
            try:
                row.file.storage.delete(row.file.name)
            except Exception:
                logger.warning("Could not remove orphaned upload %s", row.file.name, exc_info=True)
        raise
