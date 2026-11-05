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
backoff period instead of one per request. Invalidations made meanwhile are
queued and replayed afterwards, at the latest when the process exits. Without
``REDIS_URL`` the backend is DummyCache and every read misses.
"""

import atexit
import functools
import hashlib
import logging
import threading
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
    # Invalidations that haven't reached Redis yet; replayed before the next
    # cache call once the backoff is over, so a deleted list can't come back.
    _pending_invalidations = set()
    _lock = threading.Lock()

    @classmethod
    def _lookup_key(cls, table_name: str) -> str:
        return f"{cls.LOOKUP_PREFIX}:{_lookup_schema_fingerprint()}:{table_name}"

    @classmethod
    def _backing_off(cls) -> bool:
        return time.monotonic() < cls._skip_until

    @classmethod
    def _fail(cls, operation: str, table_name: str):
        cls._skip_until = time.monotonic() + cls.FAILURE_BACKOFF
        logger.warning(
            "Lookup cache %s failed for %s; skipping the cache for %ss",
            operation, table_name, cls.FAILURE_BACKOFF, exc_info=True,
        )

    @classmethod
    def _flush_pending_invalidations(cls) -> bool:
        """Delete the queued keys; False (and back off) if Redis still fails."""
        with cls._lock:
            pending = list(cls._pending_invalidations)
        for table_name in pending:
            try:
                cache.delete(cls._lookup_key(table_name))
            except Exception:
                cls._fail("invalidation", table_name)
                return False
            with cls._lock:
                cls._pending_invalidations.discard(table_name)
        return True

    @classmethod
    def _run(cls, operation: str, table_name: str, call, default=None):
        """Run one cache call; on any error log it, back off and return ``default``."""
        if cls._backing_off() or not cls._flush_pending_invalidations():
            return default
        try:
            return call()
        except Exception:
            cls._fail(operation, table_name)
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
        # Queued, then flushed now or, during a backoff, before this process's
        # next cache call (or at exit, see _flush_pending_at_exit). A bulk import
        # against an unreachable Redis thus waits no socket timeouts. Reads miss
        # while backing off, so this process never serves the stale list; other
        # pods can until the queue is flushed.
        with cls._lock:
            cls._pending_invalidations.add(table_name)
        if cls._backing_off():
            logger.warning(
                "Lookup cache invalidation for %s queued until the cache is reachable",
                table_name,
            )
            return
        cls._flush_pending_invalidations()


def _flush_pending_at_exit():
    """Last attempt for invalidations a process still holds when it exits.

    A management command (e.g. programmerimporter) or a stopping worker would
    otherwise drop them, leaving the lists stale on every pod until expiry.
    """
    if not CacheService._pending_invalidations:
        return
    CacheService._skip_until = 0.0
    if not CacheService._flush_pending_invalidations():
        logger.error(
            "Exiting with lookup cache invalidations that never reached the cache: %s; "
            "those lists may be stale for up to %ss",
            sorted(CacheService._pending_invalidations), CacheService.CACHE_TIMEOUT,
        )


atexit.register(_flush_pending_at_exit)
