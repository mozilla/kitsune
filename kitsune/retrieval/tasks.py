"""Celery entry points for retrieval ingestion work.

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
from kitsune.retrieval.sync import (
    delete_document_chunks,
    max_batch_documents,
    ordered_document_ids,
    sync_document_batch,
    sync_document_chunks,
)
from kitsune.sumo.decorators import skip_if_read_only_mode

# The embedding adapter owns provider retries so a Celery retry cannot multiply paid calls.
# Sync writes are idempotent, making incomplete writes and transport outages safe to replay.
_RETRYABLE = (
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
_SINGLE_DOCUMENT_RETRY = {
    **_RETRY,
    "autoretry_for": (DocumentLockUnavailable, *_RETRYABLE),
}


@shared_task(**_LIMITS, **_SINGLE_DOCUMENT_RETRY)
@skip_if_read_only_mode
def sync_document(document_id: int, target_index: str | None = None):
    """Sync one KB document, optionally pinned to an explicit rebuild generation."""
    if settings.RETRIEVAL_LIVE_INDEXING or target_index is not None:
        sync_document_chunks(document_id, target_index=target_index)


@shared_task(**_LIMITS, **_SINGLE_DOCUMENT_RETRY)
@skip_if_read_only_mode
def delete_document(
    content_type: str, object_id: str, locale: str, target_index: str | None = None
):
    """Evict one document from a named index, or from the write index by default.

    Deliberately not gated on ``RETRIEVAL_LIVE_INDEXING``: removing content that should no
    longer be served is not a freshness optimization. Reconciliation pins its physical target.
    """
    identity = ChunkIdentity(content_type=content_type, object_id=object_id, locale=locale)
    delete_document_chunks(identity, target_index=target_index)


def enqueue_document_sync(document_id: int) -> None:
    """Queue a sync, or drop it silently when live indexing is off.

    Signals go through here so the flag is honoured before a task is even queued, rather than
    filling the queue with work that will no-op.
    """
    if not settings.RETRIEVAL_LIVE_INDEXING:
        return
    sync_document.delay(document_id)


def enqueue_document_delete(identity: ChunkIdentity, *, target_index: str | None = None) -> None:
    delete_document.delay(
        identity.content_type,
        identity.object_id,
        identity.locale,
        target_index=target_index,
    )


@shared_task(**_LIMITS, **_RETRY)
@skip_if_read_only_mode
def sync_documents(document_ids, target_index: str | None = None):
    """Share embeddings across documents, then redispatch unfinished work individually."""
    report = sync_document_batch(document_ids, target_index=target_index)
    for document_id in report.redispatch:
        sync_document.delay(document_id, target_index=report.index)


def enqueue_document_batch(document_ids, *, target_index: str | None = None) -> None:
    """Queue bounded batches for explicit backfill or reconciliation work.

    Slicing here rather than inside the task keeps every queued payload within the configured
    document bound however large the caller's list is.
    """
    ids = ordered_document_ids(document_ids)
    size = max_batch_documents()
    for start in range(0, len(ids), size):
        sync_documents.delay(
            list(ids[start : start + size]),
            target_index=target_index,
        )
