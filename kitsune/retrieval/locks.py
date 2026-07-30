"""Redis leases that serialize retrieval work across workers.

The compare-and-act core is redis-py's ``Lock``: every renewal and release checks the stored
token first, so a worker whose lease already expired can neither extend nor delete the lease
its successor now holds. This module adds what ``Lock`` has no notion of — a background
heartbeat so a lease survives a slow provider call, a sticky record of *why* ownership ended,
and exceptions a Celery task can branch on. Ownership is surrendered rather than assumed
whenever it cannot be proven, because the alternative is two workers writing one document.
"""

import math
import threading
from contextlib import contextmanager
from functools import cache
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from redis.exceptions import LockNotOwnedError
from redis.exceptions import RedisError as RedisBackendFailure

from kitsune.retrieval.index import ChunkIdentity
from kitsune.sumo.redis_utils import RedisError as RedisUnavailable
from kitsune.sumo.redis_utils import redis_client

NAMESPACE = "retrieval:"
KEY_PREFIX = f"{NAMESPACE}lease"
_HEARTBEAT_STOP_TIMEOUT = 5.0
# Redis expiries are milliseconds, so anything shorter truncates to a ttl of zero.
_MIN_INTERVAL_SECONDS = 0.001
# Fraction of the ttl used as the heartbeat when only a shorter ttl was requested.
_DERIVED_HEARTBEAT_RATIO = 3


class DocumentLockUnavailable(Exception):
    """Another worker holds this lease, or this worker has lost it."""


class DocumentLockBackendError(Exception):
    """The lock backend could not be reached, so ownership cannot be proven."""


@cache
def _lock_client():
    """One shared Redis client for every lease.

    ``redis_client`` builds a fresh connection pool and issues a connectivity probe on each
    call. Reusing the client avoids that work per document; redis-py pools reconnect on
    their own, and a raised error is not cached, so a backend that was down is retried.
    """
    return redis_client("default")


def _validated_seconds(value, name: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(value)
        or value < _MIN_INTERVAL_SECONDS
    ):
        raise ImproperlyConfigured(
            f"{name} must be a positive, finite number of seconds of at least one millisecond"
        )
    return float(value)


def _validated_intervals(ttl_seconds, heartbeat_seconds) -> tuple[float, float]:
    """Resolve and check the lease ttl and its heartbeat interval.

    A configured pair that cannot renew in time is a deployment error and fails loudly. A
    caller asking for a shorter ttl than the configured one gets a proportionally shorter
    heartbeat, so a short lease does not oblige every call site to compute one.
    """
    if ttl_seconds is None:
        ttl = _validated_seconds(settings.RETRIEVAL_LOCK_TTL_SECONDS, "RETRIEVAL_LOCK_TTL_SECONDS")
    else:
        ttl = _validated_seconds(ttl_seconds, "ttl_seconds")

    if heartbeat_seconds is not None:
        heartbeat = _validated_seconds(heartbeat_seconds, "heartbeat_seconds")
    else:
        heartbeat = _validated_seconds(
            settings.RETRIEVAL_LOCK_HEARTBEAT_SECONDS, "RETRIEVAL_LOCK_HEARTBEAT_SECONDS"
        )
        if ttl_seconds is not None:
            heartbeat = _validated_seconds(
                min(heartbeat, ttl / _DERIVED_HEARTBEAT_RATIO),
                "the heartbeat derived from the ttl",
            )

    if heartbeat >= ttl:
        raise ImproperlyConfigured(
            "the retrieval lock heartbeat must be shorter than the lease ttl"
        )
    return ttl, heartbeat


class RedisLease:
    """One held lease. Callers get this from ``redis_lease`` / ``document_lock``."""

    def __init__(self, lock, key: str, token: str, heartbeat_seconds: float):
        self._lock = lock
        self._key = key
        self._token = token
        self._heartbeat_seconds = heartbeat_seconds
        self._state_lock = threading.Lock()
        self._lost = False
        self._backend_failed = False
        self._released = False
        self._stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None

    @property
    def token(self) -> str:
        return self._token

    @property
    def heartbeat_running(self) -> bool:
        return self._heartbeat_thread is not None and self._heartbeat_thread.is_alive()

    def __enter__(self):
        self._start_heartbeat()
        return self

    def __exit__(self, *exc_info) -> None:
        try:
            self.release()
        except DocumentLockBackendError:
            # The ttl frees the lease shortly anyway, and raising here would mask whatever
            # the caller's block was already failing with.
            pass

    def owns_lease(self) -> bool:
        """Whether this worker still provably holds the lease.

        Raises ``DocumentLockBackendError`` rather than returning ``False`` when the backend
        is unreachable: "not owned" and "cannot tell" need different handling, since only the
        latter is worth retrying.
        """
        if self._check_lost("confirm ownership of"):
            return False
        try:
            held = self._lock.owned()
        except RedisBackendFailure as exc:
            self._surrender(backend_failed=True)
            raise DocumentLockBackendError(f"cannot confirm ownership of {self._key}") from exc
        if not held:
            self._surrender()
            return False
        # The heartbeat can surrender the lease while this thread waits on the round trip, so
        # recheck before letting a caller proceed to a write.
        return not self._check_lost("confirm ownership of")

    def renew(self) -> None:
        if self._check_lost("renew"):
            raise self._lost_error()
        try:
            self._lock.reacquire()
        # LockNotOwnedError subclasses RedisError, so it has to be caught first or a lost
        # lease would be misreported as a retryable backend failure.
        except LockNotOwnedError as exc:
            self._surrender()
            raise self._lost_error() from exc
        except RedisBackendFailure as exc:
            self._surrender(backend_failed=True)
            raise DocumentLockBackendError(f"cannot renew {self._key}") from exc
        if self._check_lost("renew"):
            raise self._lost_error()

    def release(self) -> None:
        """Delete the key, but only if this worker still owns it.

        The delete is attempted even when ownership is already in doubt — the token check
        makes that safe, and skipping it would leave the key held until its ttl elapses.
        Calling this twice is a no-op, so an explicit release before leaving the context is
        allowed.
        """
        # redis-py's Lock clears its local token during release. Stop the other thread
        # before that mutation so it cannot concurrently try to renew an unlocked Lock.
        self._stop_heartbeat()
        if self._claim_release():
            return
        try:
            self._lock.release()
        except LockNotOwnedError:
            pass  # a successor holds it, so there is nothing of ours to delete
        except RedisBackendFailure as exc:
            self._surrender(backend_failed=True)
            raise DocumentLockBackendError(f"cannot release {self._key}") from exc
        self._surrender()

    def _check_lost(self, action: str) -> bool:
        """Whether the lease is known lost, raising if it was lost to a backend failure.

        A backend failure leaves ownership merely unproven, which the caller must be able to
        retry; a lease genuinely taken over is terminal. The heartbeat runs in another thread
        and cannot raise into the caller's, so it records the reason here instead.
        """
        with self._state_lock:
            lost, backend_failed = self._lost, self._backend_failed
        if backend_failed:
            raise DocumentLockBackendError(
                f"cannot {action} {self._key}: the lock backend previously failed"
            )
        return lost

    def _lost_error(self) -> DocumentLockUnavailable:
        return DocumentLockUnavailable(f"{self._key} is no longer held by this worker")

    def _surrender(self, *, backend_failed: bool = False) -> None:
        with self._state_lock:
            self._lost = True
            self._backend_failed = self._backend_failed or backend_failed

    def _claim_release(self) -> bool:
        """Whether release already ran. ``Lock.release`` clears its own token, so calling it
        twice would raise about an unlocked lock rather than no-op."""
        with self._state_lock:
            claimed, self._released = self._released, True
        return claimed

    def _start_heartbeat(self) -> None:
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop, name=f"retrieval-lease-{self._key}", daemon=True
        )
        self._heartbeat_thread.start()

    def _heartbeat_loop(self) -> None:
        # Renews on its own cadence so a lease survives a blocking provider or ES call
        # instead of only being extended between them.
        while not self._stop.wait(self._heartbeat_seconds):
            try:
                self.renew()
            except DocumentLockUnavailable, DocumentLockBackendError:
                return

    def _stop_heartbeat(self) -> None:
        self._stop.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join(timeout=_HEARTBEAT_STOP_TIMEOUT)


@contextmanager
def redis_lease(key: str, *, ttl_seconds=None, heartbeat_seconds=None):
    """Hold ``key`` for the duration of the block, renewing it in the background.

    Raises before doing any work if the key or intervals are unusable,
    ``DocumentLockUnavailable`` if another worker holds the key, and
    ``DocumentLockBackendError`` if Redis cannot be reached — never yielding an unheld lease.
    """
    if (
        not isinstance(key, str)
        or not key.startswith(NAMESPACE)
        or not key.removeprefix(NAMESPACE).strip()
    ):
        raise ValueError(f"a lease key must be a non-empty string in the {NAMESPACE!r} namespace")
    ttl, heartbeat = _validated_intervals(ttl_seconds, heartbeat_seconds)
    try:
        client = _lock_client()
    except (RedisUnavailable, RedisBackendFailure) as exc:
        raise DocumentLockBackendError(f"cannot reach the lock backend for {key}") from exc

    token = uuid4().hex
    # thread_local=False: the heartbeat renews from a background thread, and redis-py's
    # default keeps the token in thread-local state that thread could not see.
    lock = client.lock(key, timeout=ttl, blocking=False, thread_local=False)
    try:
        acquired = lock.acquire(token=token)
    except RedisBackendFailure as exc:
        raise DocumentLockBackendError(f"cannot acquire {key}") from exc
    if not acquired:
        raise DocumentLockUnavailable(f"{key} is held by another worker")

    # The lease owns its heartbeat and release from here on.
    with RedisLease(lock, key, token, heartbeat) as lease:
        yield lease


def document_lock_key(identity: ChunkIdentity) -> str:
    """A per-document key. Identity components cannot contain the delimiter, so no two
    identities can collide on one key."""
    return f"{KEY_PREFIX}:{identity.content_type}:{identity.object_id}:{identity.locale}"


def document_lock(identity: ChunkIdentity, *, ttl_seconds=None, heartbeat_seconds=None):
    """Serialize all retrieval work for one document across workers."""
    return redis_lease(
        document_lock_key(identity),
        ttl_seconds=ttl_seconds,
        heartbeat_seconds=heartbeat_seconds,
    )
