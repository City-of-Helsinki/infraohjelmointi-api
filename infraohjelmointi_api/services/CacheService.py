"""
Caching for lookup lists (phases, categories, persons, programmers, ...).

Lookup lists are read on every app load and change rarely, so their serialized
``list()`` responses are cached. ``CachedLookupViewSet`` and the model signals
in ``signals.py`` invalidate them on writes.

Financial sums are not cached: list endpoints compute them in a few batched
queries (``FinancialSumBatchService``), which is as fast as the old cache was
and cannot go stale.

A cache failure never fails a request. Errors are logged and read as misses,
and after one the process leaves the cache alone for ``FAILURE_BACKOFF``
seconds, so an unreachable Redis costs one socket timeout per process per
backoff period instead of one per request. Without ``REDIS_URL`` the backend
is DummyCache and every read misses.
"""

import functools
import hashlib
import logging
import time
from typing import Any, Optional

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Bump to drop every cached lookup on the next deploy, for a change in what a
# lookup returns that keeps its field names (field changes are picked up by
# the fingerprint below automatically).
LOOKUP_CACHE_EPOCH = 1


@functools.cache
def _lookup_schema_fingerprint() -> str:
    """Hash of every cached lookup's serializer fields.

    Part of each key, so a deploy that changes a lookup's response shape reads
    and writes new keys instead of serving the old shape until the TTL runs
    out, and pods still on the old release during a rolling deploy cannot
    overwrite the new shape. The flip side: an edit that lands on an old pod
    mid-rollout only clears the old key, so the new key can hold the pre-edit
    list until the edit is repeated or CACHE_TIMEOUT runs out.
    """
    # Lazy import: views import this module.
    from infraohjelmointi_api.views.CachedLookupViewSet import cached_lookup_viewsets

    def fields(serializer) -> list:
        nested = getattr(serializer, "child", serializer)
        if not hasattr(nested, "fields"):
            return []
        return sorted(
            (name, fields(field)) for name, field in nested.fields.items()
        )

    shapes = sorted(
        (viewset.__name__, fields(viewset.serializer_class()))
        for viewset in cached_lookup_viewsets()
        if getattr(viewset, "serializer_class", None)
    )
    digest = hashlib.sha256(repr((LOOKUP_CACHE_EPOCH, shapes)).encode()).hexdigest()
    return digest[:12]


class CacheService:
    LOOKUP_PREFIX = "lookup"
    CACHE_TIMEOUT = getattr(settings, "CACHE_TIMEOUT", 43200)
    FAILURE_BACKOFF = 30

    _skip_until = 0.0

    @classmethod
    def _lookup_key(cls, table_name: str) -> str:
        return f"{cls.LOOKUP_PREFIX}:{_lookup_schema_fingerprint()}:{table_name}"

    @classmethod
    def _run(cls, operation: str, table_name: str, call, default=None):
        """Run one cache call; on any error log it, back off and return ``default``."""
        if time.monotonic() < cls._skip_until:
            return default
        try:
            return call()
        except Exception:
            cls._skip_until = time.monotonic() + cls.FAILURE_BACKOFF
            logger.warning(
                "Lookup cache %s failed for %s; skipping the cache for %ss",
                operation, table_name, cls.FAILURE_BACKOFF, exc_info=True,
            )
            return default

    @classmethod
    def get_lookup(cls, table_name: str) -> Optional[Any]:
        return cls._run("read", table_name, lambda: cache.get(cls._lookup_key(table_name)))

    @classmethod
    def set_lookup(cls, table_name: str, data: Any) -> None:
        cls._run(
            "write", table_name,
            lambda: cache.set(cls._lookup_key(table_name), data, cls.CACHE_TIMEOUT),
        )

    @classmethod
    def invalidate_lookup(cls, table_name: str) -> None:
        # Also backed off: a bulk import saving hundreds of rows would otherwise
        # wait one socket timeout per row while Redis is unreachable. A skipped
        # or failed delete can leave the list stale for up to CACHE_TIMEOUT.
        if time.monotonic() < cls._skip_until:
            logger.error(
                "Lookup cache invalidation skipped for %s (cache backing off); "
                "the cached list may be stale for up to %ss", table_name, cls.CACHE_TIMEOUT,
            )
            return
        try:
            cache.delete(cls._lookup_key(table_name))
        except Exception:
            cls._skip_until = time.monotonic() + cls.FAILURE_BACKOFF
            logger.error(
                "Lookup cache invalidation failed for %s; the cached list may "
                "be stale for up to %ss", table_name, cls.CACHE_TIMEOUT, exc_info=True,
            )
