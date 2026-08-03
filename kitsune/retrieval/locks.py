"""Redis leases that serialize retrieval work across workers.

The compare-and-act core is redis-py's ``Lock``: every renewal and release checks the stored
token first, so a worker whose lease already expired can neither extend nor delete the lease
its successor now holds. This module adds a namespaced key contract, a validated ttl, and
exceptions a Celery task can branch on.

There is no background renewer. Callers must finish before the ttl and renew immediately
before writing to prove ownership. The lease serializes writers; it is not authorization
state.
"""

import logging
import math
from contextlib import contextmanager
from functools import cache
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from redis.exceptions import LockNotOwnedError
from redis.exceptions import RedisError as RedisBackendFailure

from kitsune.retrieval.events import emit
from kitsune.retrieval.index import ChunkIdentity
from kitsune.sumo.redis_utils import RedisError as RedisUnavailable
from kitsune.sumo.redis_utils import redis_client

NAMESPACE = "retrieval:"
KEY_PREFIX = f"{NAMESPACE}lease"
_LIFECYCLE_KEY = f"{KEY_PREFIX}:lifecycle"
# Redis expiries are milliseconds, so anything shorter truncates to a ttl of zero — and
# PEXPIRE with zero deletes the key outright.
_MIN_TTL_SECONDS = 0.001


def _lock_kind(key: str) -> str:
    """Return bounded context without logging the identity-bearing Redis key."""
    if key == _LIFECYCLE_KEY:
        return "lifecycle"
    if key.startswith(f"{KEY_PREFIX}:"):
        return "document"
    return "other"


class DocumentLockUnavailable(Exception):
    """Another worker holds this lease, or this worker has lost it."""


class DocumentLockBackendError(Exception):
    """The lock backend could not be reached, so ownership cannot be proven."""


@cache
def _lock_client():
    """One shared Redis client for every lease.

    ``redis_client`` builds a connection pool and probes Redis on every call. Reusing the
    client avoids that setup; redis-py pools reconnect on their own, and failed calls are
    not cached.
    """
    return redis_client("default")


def _validated_ttl(ttl_seconds, *, name: str = "ttl_seconds") -> float:
    # Name the source in the error so a reader knows whether to fix the setting or the call.
    # A caller reading its own setting passes that setting's name.
    if ttl_seconds is None:
        ttl_seconds, name = settings.RETRIEVAL_LOCK_TTL_SECONDS, "RETRIEVAL_LOCK_TTL_SECONDS"
    if (
        isinstance(ttl_seconds, bool)
        or not isinstance(ttl_seconds, int | float)
        or not math.isfinite(ttl_seconds)
        or ttl_seconds < _MIN_TTL_SECONDS
    ):
        raise ImproperlyConfigured(
            f"{name} must be a positive, finite number of seconds of at least one millisecond"
        )
    return float(ttl_seconds)


class RedisLease:
    """One held lease. Callers get this from ``redis_lease`` / ``document_lock``."""

    def __init__(self, lock, key: str, token: str):
        self.token = token
        self._lock = lock
        self._key = key
        self._released = False

    def renew(self) -> None:
        """Prove ownership and extend the lease in one round trip.

        This is the checkpoint primitive: a caller about to write calls this rather than
        reading ownership separately, because the underlying script compares the token and
        resets the expiry atomically.
        """
        try:
            self._lock.reacquire()
        # LockNotOwnedError subclasses RedisError, so it has to be caught first or a lost
        # lease would be misreported as a retryable backend failure.
        except LockNotOwnedError as exc:
            emit(
                "retrieval.lock.lost",
                level=logging.WARNING,
                lock_kind=_lock_kind(self._key),
            )
            raise DocumentLockUnavailable(f"{self._key} is no longer held by this worker") from exc
        except RedisBackendFailure as exc:
            emit(
                "retrieval.lock.backend_unavailable",
                level=logging.ERROR,
                lock_kind=_lock_kind(self._key),
                operation="renew",
                error_type=type(exc).__name__,
            )
            raise DocumentLockBackendError(f"cannot renew {self._key}") from exc

    def release(self) -> None:
        """Delete the key, but only if this worker still owns it.

        Idempotent: ``Lock.release`` clears its own token first, so calling it twice would
        otherwise complain about an unlocked lock.
        """
        if self._released:
            return
        self._released = True
        try:
            self._lock.release()
        except LockNotOwnedError:
            pass  # a successor holds it, so there is nothing of ours to delete
        except RedisBackendFailure as exc:
            emit(
                "retrieval.lock.backend_unavailable",
                level=logging.ERROR,
                lock_kind=_lock_kind(self._key),
                operation="release",
                error_type=type(exc).__name__,
            )
            raise DocumentLockBackendError(f"cannot release {self._key}") from exc


@contextmanager
def redis_lease(key: str, *, ttl_seconds=None):
    """Hold ``key`` for the duration of the block, releasing it on the way out.

    Never yields an unheld lease: an unusable key or ttl, contention, and an unreachable
    backend all raise instead.
    """
    if (
        not isinstance(key, str)
        or not key.startswith(NAMESPACE)
        or not key.removeprefix(NAMESPACE).strip()
    ):
        raise ValueError(f"a lease key must be a non-empty string in the {NAMESPACE!r} namespace")
    ttl = _validated_ttl(ttl_seconds)

    token = uuid4().hex
    try:
        lock = _lock_client().lock(key, timeout=ttl, blocking=False)
        acquired = lock.acquire(token=token)
    except (RedisUnavailable, RedisBackendFailure) as exc:
        emit(
            "retrieval.lock.backend_unavailable",
            level=logging.ERROR,
            lock_kind=_lock_kind(key),
            operation="acquire",
            error_type=type(exc).__name__,
        )
        raise DocumentLockBackendError(f"cannot acquire {key}") from exc
    if not acquired:
        emit(
            "retrieval.lock.contended",
            level=logging.WARNING,
            lock_kind=_lock_kind(key),
        )
        raise DocumentLockUnavailable(f"{key} is held by another worker")

    lease = RedisLease(lock, key, token)
    try:
        yield lease
    finally:
        try:
            lease.release()
        except DocumentLockBackendError:
            # Protected work has already finished (or raised); the ttl provides cleanup.
            pass


def document_lock_key(identity: ChunkIdentity) -> str:
    """A per-document key. Identity components cannot contain the delimiter, so no two
    identities can collide on one key."""
    return f"{KEY_PREFIX}:{identity.content_type}:{identity.object_id}:{identity.locale}"


def document_lock(identity: ChunkIdentity, *, ttl_seconds=None):
    """Serialize all retrieval work for one document across workers."""
    return redis_lease(document_lock_key(identity), ttl_seconds=ttl_seconds)


def lifecycle_lock(*, ttl_seconds=None):
    """Coordinate generation creation and alias moves across operators.

    One key protects the shared alias state rather than any particular generation. Like every
    lease here it expires; callers must renew after a long read-only phase and before a change.
    """
    if ttl_seconds is None:
        # Validated here, not in redis_lease, so the error names the setting to fix.
        ttl_seconds = _validated_ttl(
            settings.RETRIEVAL_LIFECYCLE_LOCK_TTL_SECONDS,
            name="RETRIEVAL_LIFECYCLE_LOCK_TTL_SECONDS",
        )
    return redis_lease(_LIFECYCLE_KEY, ttl_seconds=ttl_seconds)
