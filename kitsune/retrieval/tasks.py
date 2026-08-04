"""Celery entry points for retrieval ingestion work.

Each task carries its own soft and hard limits rather than relying on global Celery limits,
which would truncate unrelated Kitsune tasks. Those limits sit below the lease ttl, which is
what lets the lease go unrenewed in the background (see ``checks.py``).

Arguments are JSON-safe primitives so a queued task never depends on unpickling a value object.
Results are ignored because sync outcomes are emitted as structured events.
"""

import logging
import random

from celery import shared_task
from django.conf import settings
from elastic_transport import ConnectionError as ElasticsearchConnectionError
from elastic_transport import ConnectionTimeout as ElasticsearchConnectionTimeout

from kitsune.retrieval.events import emit
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
# Batch contention is retried separately so completed work is never repeated.
_BULK_RETRY_SECONDS = 30

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
def sync_document(document_id: int):
    """Bring every active index into agreement with one KB document."""
    if settings.RETRIEVAL_LIVE_INDEXING:
        sync_document_chunks(document_id)


@shared_task(**_LIMITS, **_SINGLE_DOCUMENT_RETRY)
@skip_if_read_only_mode
def delete_document(content_type: str, object_id: str, locale: str, target_indexes=None):
    """Evict one document from the named indexes, or from every active index by default.

    Deliberately not gated on ``RETRIEVAL_LIVE_INDEXING``: removing content that should no
    longer be served is not a freshness optimization. Reconciliation pins the target, because
    evicting from one generation must not empty the other.
    """
    identity = ChunkIdentity(content_type=content_type, object_id=object_id, locale=locale)
    delete_document_chunks(identity, target_indexes=target_indexes)


def enqueue_document_sync(document_id: int) -> None:
    """Queue a sync, or drop it silently when live indexing is off.

    Signals go through here so the flag is honoured before a task is even queued, rather than
    filling the queue with work that will no-op.
    """
    if not settings.RETRIEVAL_LIVE_INDEXING:
        return
    sync_document.delay(document_id)


def enqueue_document_delete(identity: ChunkIdentity, *, target_indexes=None) -> None:
    delete_document.delay(
        identity.content_type,
        identity.object_id,
        identity.locale,
        target_indexes=list(target_indexes) if target_indexes is not None else None,
    )


@shared_task(**_LIMITS, **_RETRY)
@skip_if_read_only_mode
def sync_documents(document_ids, target_indexes=None, contention_attempt: int = 0):
    """Bring a batch of KB documents into agreement, sharing embedding calls across them.

    Deferred work is queued immediately. Contended documents retry separately with jitter, so
    neither path repeats work that this attempt already committed.
    """
    report = sync_document_batch(document_ids, target_indexes=target_indexes)
    if report.deferred:
        enqueue_document_batch(report.deferred, target_indexes=target_indexes)

    if not report.contended:
        return
    if contention_attempt >= sync_documents.max_retries:
        emit(
            "retrieval.batch.abandoned",
            level=logging.WARNING,
            reason="contention",
            document_count=len(report.contended),
        )
        return
    sync_documents.apply_async(
        args=[list(report.contended)],
        kwargs={
            "target_indexes": target_indexes,
            "contention_attempt": contention_attempt + 1,
        },
        countdown=random.uniform(1, _BULK_RETRY_SECONDS),
    )


def enqueue_document_batch(document_ids, *, target_indexes=None) -> None:
    """Queue bounded batches for explicit backfill or reconciliation work.

    Slicing here rather than inside the task keeps every queued payload within the configured
    document bound however large the caller's list is.
    """
    ids = ordered_document_ids(document_ids)
    targets = list(target_indexes) if target_indexes is not None else None
    size = max_batch_documents()
    for start in range(0, len(ids), size):
        sync_documents.delay(
            list(ids[start : start + size]),
            target_indexes=targets,
        )
