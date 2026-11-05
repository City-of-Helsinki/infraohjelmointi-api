"""
Token-to-user resolution for helusers' ApiTokenAuthentication, with a cache.

helusers' default resolver syncs the user from the token on every API request:
about ten queries, including ``select_for_update`` on the user row while it
re-syncs the AD groups. A page load fires ~35 requests in parallel, which then
queue on that lock one by one.

The sync's outcome depends only on the token's claims, so it is done once per
token (per process) and later requests with the same token only load the user
by id. A new token, e.g. after a refresh or with changed AD groups, syncs
again. JWT validation and the back-channel logout check still run on every
request; they happen before the resolver is called.
"""

import hashlib
import json
import threading
import time

from django.contrib.auth import get_user_model
from helusers.oidc import resolve_user as sync_user

# Also bounds how long a change made in the database alone (e.g. an
# ADGroupMapping edited in the admin) waits for the next sync.
CACHE_SECONDS = 300
MAX_ENTRIES = 1000

_lock = threading.Lock()
_user_ids = {}  # claims hash -> (user id, expires at)
_key_locks = {}  # claims hash -> lock held while that token is synced


def resolve_user(request, payload):
    key = _claims_key(payload)
    user = _cached_user(key)
    if user is not None:
        return user

    # One sync per token: parallel first requests wait for it, then load the
    # user it produced, instead of all syncing behind the user-row lock.
    with _lock:
        key_lock = _key_locks.setdefault(key, threading.Lock())
    try:
        with key_lock:
            user = _cached_user(key)
            if user is None:
                user = sync_user(request, payload)
                _remember(key, user.pk)
            return user
    finally:
        with _lock:
            # A waiter must not drop a lock a later request already replaced it with.
            if _key_locks.get(key) is key_lock:
                del _key_locks[key]


def clear():
    with _lock:
        _user_ids.clear()


def _claims_key(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def _cached_user(key):
    with _lock:
        entry = _user_ids.get(key)
    if entry is None or entry[1] <= time.monotonic():
        return None
    try:
        return get_user_model().objects.get(pk=entry[0])
    except get_user_model().DoesNotExist:
        return None


def _remember(key, user_id):
    now = time.monotonic()
    with _lock:
        if len(_user_ids) >= MAX_ENTRIES:
            for stale in [k for k, (_, expires) in _user_ids.items() if expires <= now]:
                del _user_ids[stale]
            if len(_user_ids) >= MAX_ENTRIES:
                _user_ids.clear()
        _user_ids[key] = (user_id, now + CACHE_SECONDS)
