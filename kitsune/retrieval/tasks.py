"""Celery entry points for incremental retrieval work.

Each task carries its own soft and hard limits rather than relying on global Celery limits,
which would truncate unrelated Kitsune tasks. Those limits sit below the lease ttl, which is
what lets the lease go unrenewed in the background (see ``checks.py``).

Arguments are JSON-safe primitives so a queued task never depends on unpickling a value object.
Results are ignored because sync outcomes are emitted as structured events.
"""

from celery import shared_task
from django.conf import settings
from elastic_transport import ConnectionError as ElasticsearchConnectionError
from elastic_transport import ConnectionTimeout as ElasticsearchConnectionTimeout

from kitsune.retrieval.index import ChunkIdentity, IndexWriteError
from kitsune.retrieval.locks import DocumentLockBackendError, DocumentLockUnavailable
from kitsune.retrieval.sync import delete_document_chunks, sync_document_chunks
from kitsune.sumo.decorators import skip_if_read_only_mode

# The embedding adapter owns provider retries so a Celery retry cannot multiply paid calls.
# Sync writes are idempotent, making incomplete writes and transport outages safe to replay.
_RETRYABLE = (
    DocumentLockUnavailable,
    DocumentLockBackendError,
    IndexWriteError,
    ElasticsearchConnectionError,
    ElasticsearchConnectionTimeout,
)

_LIMITS = {
    "soft_time_limit": settings.RETRIEVAL_TASK_SOFT_TIME_LIMIT_SECONDS,
    "time_limit": settings.RETRIEVAL_TASK_TIME_LIMIT_SECONDS,
    "ignore_result": True,
}
_RETRY = {
    "autoretry_for": _RETRYABLE,
    "retry_backoff": True,
    "retry_jitter": True,
    "max_retries": 5,
}


@shared_task(**_LIMITS, **_RETRY)
@skip_if_read_only_mode
def sync_document(document_id: int):
    """Bring every active index into agreement with one KB document."""
    if settings.RETRIEVAL_LIVE_INDEXING:
        sync_document_chunks(document_id)


@shared_task(**_LIMITS, **_RETRY)
@skip_if_read_only_mode
def delete_document(content_type: str, object_id: str, locale: str):
    """Evict one document from every active index.

    Deliberately not gated on ``RETRIEVAL_LIVE_INDEXING``: removing content that should no
    longer be served is not a freshness optimization. Reused by reconciliation and by the sync
    core's eviction path.
    """
    identity = ChunkIdentity(content_type=content_type, object_id=object_id, locale=locale)
    delete_document_chunks(identity)


def enqueue_document_sync(document_id: int) -> None:
    """Queue a sync, or drop it silently when live indexing is off.

    Signals go through here so the flag is honoured before a task is even queued, rather than
    filling the queue with work that will no-op.
    """
    if not settings.RETRIEVAL_LIVE_INDEXING:
        return
    sync_document.delay(document_id)


def enqueue_document_delete(identity: ChunkIdentity) -> None:
    delete_document.delay(identity.content_type, identity.object_id, identity.locale)
