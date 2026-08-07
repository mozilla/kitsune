"""Decide and perform what documents need in the current retrieval write index.

The decision is separated from the work. ``plan_target`` is pure: given what a worker computed
and what an index currently holds, it names an outcome and touches nothing. That keeps the
whole outcome matrix testable without Elasticsearch, Redis, or the database, and leaves the
executor with no judgement of its own to make.

One document and a batch of documents run the same decisions on the same seams; a batch only
shares the provider calls, so it is cheaper without being weaker.
"""

import logging
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from kitsune.retrieval.chunking import CHUNKING_GENERATION, Chunk, chunk
from kitsune.retrieval.eligibility import (
    access_group_ids_for,
    family_id_for,
    is_retrieval_indexable,
    visibility_for,
)
from kitsune.retrieval.embeddings import (
    EmbeddingRecipe,
    get_embeddings,
)
from kitsune.retrieval.events import emit
from kitsune.retrieval.fingerprints import (
    content_hash,
    index_state_hash,
)
from kitsune.retrieval.index import (
    ChunkIdentity,
    ChunkSource,
    ExpectedDocumentState,
    IncompleteDocumentState,
    StoredChunkSummary,
    access_metadata_matches,
    chunk_layout_matches,
    delete_chunks_for,
    delete_chunks_for_object,
    read_chunk_summaries,
    read_manifest,
    recipe_for_index,
    replace_chunks,
    resolve_write_target,
    update_chunks_metadata_for,
)
from kitsune.retrieval.locks import DocumentLockUnavailable, document_lock
from kitsune.wiki.models import Document

CONTENT_TYPE = "kb"


class SyncOutcome(StrEnum):
    """What one document needs in one physical index."""

    EMBED_REPLACE = "embed_replace"
    METADATA_ONLY = "metadata_only"
    NO_OP = "no_op"
    DELETED = "deleted"
    ABORTED_STALE = "aborted_stale"


def _stored_is_newer(
    manifest: ExpectedDocumentState | None, expected: ExpectedDocumentState
) -> bool:
    return bool(
        manifest
        and (
            manifest.chunking_generation > expected.chunking_generation
            or manifest.indexed_revision_id > expected.indexed_revision_id
        )
    )


def plan_target(
    *,
    chunks: list[Chunk],
    source: ChunkSource,
    expected_state: ExpectedDocumentState,
    manifest: ExpectedDocumentState | None,
    summaries: tuple[StoredChunkSummary, ...],
) -> SyncOutcome:
    """Name the cheapest outcome that makes this index correct for this document.

    A final manifest is the commit marker. Stored text and vectors are intentionally not read:
    exceptional incomplete writes are replaced instead of making every normal sync prove that
    their individual vectors are reusable.
    """
    if _stored_is_newer(manifest, expected_state):
        return SyncOutcome.ABORTED_STALE

    if manifest is None or manifest.content_hash != expected_state.content_hash:
        return SyncOutcome.EMBED_REPLACE

    if not chunk_layout_matches(summaries, expected_state.chunk_count):
        return SyncOutcome.EMBED_REPLACE

    access_matches = all(access_metadata_matches(summary, source) for summary in summaries)
    if manifest != expected_state or not access_matches:
        return SyncOutcome.METADATA_ONLY

    return SyncOutcome.NO_OP


@dataclass(frozen=True)
class SyncReport:
    """What one single-target sync attempt did."""

    identity: ChunkIdentity | None
    index: str | None = None
    outcome: SyncOutcome | None = None
    # Embedding-adapter calls attributable to this document. A batch's shared call belongs to
    # the batch report; a document-specific fallback remains attributable here.
    embedding_calls: int = 0


@dataclass(frozen=True)
class BatchSyncReport:
    """What one optimistic batch did and which documents need ordinary sync."""

    reports: dict[int, SyncReport] = field(default_factory=dict)
    index: str | None = None
    redispatch: tuple[int, ...] = ()
    embedding_calls: int = 0


def _report(
    identity: ChunkIdentity | None,
    index: str,
    outcome: SyncOutcome,
    embedding_calls: int = 0,
    *,
    object_id: str | None = None,
    approved_at: datetime | None = None,
) -> SyncReport:
    """Emit and return one consistent result for every terminal sync path."""
    approval_latency_ms = (
        None
        if approved_at is None
        else int((datetime.now(tz=UTC) - approved_at).total_seconds() * 1000)
    )
    emit(
        "retrieval.sync.completed",
        content_type=CONTENT_TYPE,
        object_id=identity.object_id if identity else object_id,
        locale=identity.locale if identity else None,
        index=index,
        outcome=outcome.value,
        embedding_calls=embedding_calls,
        # Approval to searchable: null on paths with no approved revision, never a false zero.
        # Negative values deliberately expose clock skew or a future-dated review.
        approval_latency_ms=approval_latency_ms,
    )
    return SyncReport(identity, index, outcome, embedding_calls)


def build_source(document) -> ChunkSource:
    """Denormalize one localized document into the metadata every chunk repeats.

    Locale-specific text comes from the document and its approved revision; anything a
    translation inherits — products, topics, category, access — comes from the original.
    """
    original = document.original
    revision = document.current_revision
    return ChunkSource(
        content_type=CONTENT_TYPE,
        object_id=str(document.id),
        locale=document.locale,
        family_id=str(family_id_for(document)),
        title=document.title,
        summary=revision.summary,
        keywords=revision.keywords,
        slug=document.slug,
        category=str(original.category),
        product_ids=tuple(str(product.id) for product in original.products.all()),
        topic_ids=tuple(str(topic.id) for topic in original.topics.all()),
        visibility=visibility_for(document),
        access_group_ids=tuple(access_group_ids_for(document)),
        updated=revision.created,
    )


def expected_state_for(
    chunks: list[Chunk], source: ChunkSource, document
) -> ExpectedDocumentState:
    """The state a healthy commit of this document would hold.

    Public because the gate has to compare against exactly what the writer would have produced.
    """
    return ExpectedDocumentState(
        content_hash=content_hash(chunks),
        index_state_hash=index_state_hash(chunks, source),
        chunking_generation=CHUNKING_GENERATION,
        chunk_count=len(chunks),
        indexed_revision_id=document.current_revision_id,
        updated=source.updated,
    )


def _load_many(document_ids) -> dict[int, Document]:
    documents = (
        Document.objects.filter(pk__in=list(document_ids))
        .select_related("parent", "current_revision")
        .prefetch_related(
            "products",
            "topics",
            "restrict_to_groups",
            "parent__products",
            "parent__topics",
            "parent__restrict_to_groups",
        )
    )
    return {document.id: document for document in documents}


def _load(document_id: int):
    return _load_many([document_id]).get(document_id)


def _identity_for(document) -> ChunkIdentity:
    return ChunkIdentity(CONTENT_TYPE, str(document.id), document.locale)


def _resolve_target(target_index: str | None) -> str | None:
    """Use an explicit physical index or snapshot the write alias once."""
    return target_index if target_index is not None else resolve_write_target()


def _evict(identity: ChunkIdentity, index: str, embedding_calls: int = 0) -> SyncReport:
    delete_chunks_for(index=index, identity=identity)
    return _report(identity, index, SyncOutcome.DELETED, embedding_calls)


def _evict_object(object_id: str, index: str, embedding_calls: int = 0) -> SyncReport:
    """Remove every locale of a source row that no longer exists.

    A deleted row cannot tell us its locale, so the identity-scoped delete is unavailable.
    """
    delete_chunks_for_object(index=index, content_type=CONTENT_TYPE, object_id=object_id)
    return _report(
        None,
        index,
        SyncOutcome.DELETED,
        embedding_calls,
        object_id=object_id,
    )


@dataclass(frozen=True)
class _DocumentWork:
    """One locked document's decisions, before anything has been written."""

    document_id: int
    identity: ChunkIdentity
    source: ChunkSource
    chunks: list[Chunk]
    expected: ExpectedDocumentState
    outcome: SyncOutcome
    # Approval time, for the freshness SLI only. Deliberately not part of the indexed payload
    # or any hash: it must not make a document look changed.
    approved_at: datetime | None = None


def _embed_for_works(
    works: dict[int, _DocumentWork], recipe: EmbeddingRecipe
) -> tuple[dict[int, list[list[float]]], int]:
    """Embed all documents needing replacement in one flattened provider call."""
    inputs: list[str] = []
    spans: dict[int, tuple[int, int]] = {}
    for document_id, work in works.items():
        if work.outcome is SyncOutcome.EMBED_REPLACE:
            spans[document_id] = (len(inputs), len(inputs) + len(work.chunks))
            inputs.extend(chunk.text for chunk in work.chunks)

    if not inputs:
        return {}, 0
    combined = get_embeddings(inputs, task="document", recipe=recipe)
    return {document_id: combined[start:stop] for document_id, (start, stop) in spans.items()}, 1


def _plan_document(document, index) -> _DocumentWork | SyncReport:
    """Plan one locked, eligible document for one index—or finish it outright.

    Returns a report when the document needs no provider work: it is stale or already agrees
    with the target.
    """
    identity = _identity_for(document)
    source = build_source(document)
    chunks = chunk(CONTENT_TYPE, document.html, title=document.title)
    expected = expected_state_for(chunks, source, document)
    manifest = read_manifest(index=index, identity=identity)
    summaries = (
        read_chunk_summaries(index=index, identity=identity)
        if manifest and manifest.content_hash == expected.content_hash
        else ()
    )
    plan = plan_target(
        chunks=chunks,
        source=source,
        expected_state=expected,
        manifest=manifest,
        summaries=summaries,
    )

    if plan is SyncOutcome.ABORTED_STALE:
        return _report(identity, index, SyncOutcome.ABORTED_STALE)

    work = _DocumentWork(
        document_id=document.id,
        identity=identity,
        source=source,
        chunks=chunks,
        expected=expected,
        outcome=plan,
        approved_at=document.current_revision.reviewed,
    )
    if plan is SyncOutcome.NO_OP:
        return _report(identity, index, SyncOutcome.NO_OP)
    return work


def _revalidate(
    work: _DocumentWork, document, index, lease, embedding_calls: int = 0
) -> SyncReport | None:
    """The terminal report if the document moved while the provider worked, else ``None``.

    Recomputed from the reloaded HTML: included-content rerenders can change HTML without
    changing current_revision_id, so the revision alone is not a sufficient guard.
    """
    if document is None:
        lease.renew()
        return _evict_object(work.identity.object_id, index, embedding_calls)
    if not is_retrieval_indexable(document):
        lease.renew()
        return _evict(work.identity, index, embedding_calls)
    # Batch planning is optimistic, so another worker may have advanced the index before this
    # lease was acquired. Never let a lagging database read downgrade that committed state.
    if _stored_is_newer(
        read_manifest(index=index, identity=work.identity),
        work.expected,
    ):
        return _report(work.identity, index, SyncOutcome.ABORTED_STALE, embedding_calls)
    fresh_chunks = chunk(CONTENT_TYPE, document.html, title=document.title)
    if expected_state_for(fresh_chunks, build_source(document), document) != work.expected:
        return _report(work.identity, index, SyncOutcome.ABORTED_STALE, embedding_calls)
    return None


def _apply_plan(
    work: _DocumentWork,
    index: str,
    recipe: EmbeddingRecipe,
    lease,
    vectors=(),
) -> tuple[SyncReport | None, SyncOutcome, int]:
    """Apply an outcome, replacing once if metadata finds an incomplete layout.

    The replacement fallback embeds and then revalidates just like the main embedding path;
    the returned call count lets single and batch reports account for that extra work.
    """
    # A plan may need several ES calls. Renew immediately before starting it; the task-level
    # deadline keeps the complete mutation shorter than the lease.
    lease.renew()
    if work.outcome is SyncOutcome.EMBED_REPLACE:
        replace_chunks(
            index=index,
            chunks=work.chunks,
            vectors=vectors,
            source=work.source,
            expected_state=work.expected,
        )
        return None, work.outcome, 0
    elif work.outcome is SyncOutcome.METADATA_ONLY:
        try:
            update_chunks_metadata_for(
                index=index,
                chunks=work.chunks,
                source=work.source,
                expected_state=work.expected,
            )
            return None, work.outcome, 0
        except IncompleteDocumentState:
            fallback_vectors = get_embeddings(
                [chunk.text for chunk in work.chunks], task="document", recipe=recipe
            )
            terminal = _revalidate(
                work,
                _load(work.document_id),
                index,
                lease,
                1,
            )
            if terminal is not None:
                return terminal, work.outcome, 1
            lease.renew()
            replace_chunks(
                index=index,
                chunks=work.chunks,
                vectors=fallback_vectors,
                source=work.source,
                expected_state=work.expected,
            )
            return None, SyncOutcome.EMBED_REPLACE, 1
    raise AssertionError(f"{work.outcome} is not a writable plan")


def sync_document_chunks(document_id: int, *, target_index: str | None = None) -> SyncReport:
    """Bring one physical index into agreement with one document.

    Holds the document's lease for the whole attempt, embeds if necessary, then revalidates the
    source before writing because the row can change while a provider call is in flight.
    """
    index = _resolve_target(target_index)
    if not index:
        emit(
            "retrieval.sync.skipped",
            level=logging.WARNING,
            reason="no_write_index",
            document_id=document_id,
        )
        return SyncReport(None)

    document = _load(document_id)
    if document is None:
        return _evict_object(str(document_id), index)

    identity = _identity_for(document)
    with document_lock(identity) as lease:
        document = _load(document_id)  # authoritative read, now that nobody else may write
        if document is None:
            return _evict_object(identity.object_id, index)
        # Before the recipe, so an unreadable `_meta` cannot block removing content that
        # should no longer be served.
        if not is_retrieval_indexable(document):
            return _evict(identity, index)

        # The recipe must fail before anything is paid for.
        recipe = recipe_for_index(index)
        work = _plan_document(document, index)
        if isinstance(work, SyncReport):
            return work

        vectors, calls = _embed_for_works({document_id: work}, recipe)
        terminal = _revalidate(work, _load(document_id), index, lease, calls)
        if terminal is not None:
            return terminal
        terminal, outcome, fallback_calls = _apply_plan(
            work,
            index,
            recipe,
            lease,
            vectors.get(document_id, ()),
        )
        calls += fallback_calls
        if terminal is not None:
            return terminal

    return _report(identity, index, outcome, calls, approved_at=work.approved_at)


def ordered_document_ids(document_ids) -> tuple[int, ...]:
    """Deduplicate and sort a batch's ids.

    Duplicates would sync the same document twice in one batch, and a deterministic order keeps
    a batch, its logs, and its retry reproducible.
    """
    if isinstance(document_ids, str | bytes) or not isinstance(document_ids, Iterable):
        raise TypeError("a batch must be an iterable of document ids")
    ids = set()
    for value in document_ids:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"document id {value!r} is not an integer")
        ids.add(value)
    return tuple(sorted(ids))


def _bulk_bound(name: str) -> int:
    value = getattr(settings, name, None)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ImproperlyConfigured(f"{name} must be a positive integer")
    return value


def max_batch_documents() -> int:
    """The configured ceiling on documents per batch, so callers can size their payloads."""
    return _bulk_bound("RETRIEVAL_BULK_MAX_DOCUMENTS")


def max_batch_embedding_inputs() -> int:
    """The configured ceiling on embedding inputs in one document batch."""
    return _bulk_bound("RETRIEVAL_BULK_MAX_EMBEDDING_INPUTS")


def sync_document_batch(document_ids, *, target_index: str | None = None) -> BatchSyncReport:
    """Bring documents into agreement with one target, sharing the provider call.

    Planning and embedding are optimistic and hold no leases. Each write then gets one document
    lease, reloads the source, and commits only if the prepared state is still current. Overflow,
    source races, and contention all use the same ordinary per-document retry path.
    """
    ids = ordered_document_ids(document_ids)
    if not ids:
        return BatchSyncReport()

    max_documents = max_batch_documents()
    max_inputs = max_batch_embedding_inputs()
    index = _resolve_target(target_index)
    if not index:
        emit(
            "retrieval.batch.skipped",
            level=logging.WARNING,
            reason="no_write_index",
            document_count=len(ids),
        )
        return BatchSyncReport()

    ids, over_document_limit = ids[:max_documents], ids[max_documents:]
    reports: dict[int, SyncReport] = {}
    redispatch = list(over_document_limit)

    # Remove missing or ineligible content before reading the target recipe. Bad target metadata
    # must not prevent a safety eviction. An ineligible document is reloaded under its own short
    # lease; if it became eligible in the meantime, ordinary sync handles its new state.
    eligible = {}
    known = _load_many(ids)
    for document_id in ids:
        document = known.get(document_id)
        if document is None:
            reports[document_id] = _evict_object(str(document_id), index)
            continue
        if is_retrieval_indexable(document):
            eligible[document_id] = document
            continue
        try:
            with document_lock(_identity_for(document)):
                fresh = _load(document_id)
                if fresh is None:
                    reports[document_id] = _evict_object(str(document_id), index)
                elif is_retrieval_indexable(fresh):
                    redispatch.append(document_id)
                else:
                    reports[document_id] = _evict(_identity_for(fresh), index)
        except DocumentLockUnavailable:
            redispatch.append(document_id)

    calls = 0
    if eligible:
        recipe = recipe_for_index(index)
        planned_works: dict[int, _DocumentWork] = {}
        for document_id, document in eligible.items():
            planned = _plan_document(document, index)
            if isinstance(planned, SyncReport):
                reports[document_id] = planned
            else:
                planned_works[document_id] = planned

        # Keep the task's total embedding input bounded. Always admit the first document so an
        # unusually large article cannot be rejected forever; overflow takes ordinary sync.
        works: dict[int, _DocumentWork] = {}
        used_inputs = 0
        for document_id, work in planned_works.items():
            needed = len(work.chunks) if work.outcome is SyncOutcome.EMBED_REPLACE else 0
            if works and used_inputs + needed > max_inputs:
                redispatch.append(document_id)
                continue
            works[document_id] = work
            used_inputs += needed

        vectors, calls = _embed_for_works(works, recipe)
        for document_id, work in works.items():
            try:
                with document_lock(work.identity) as lease:
                    terminal = _revalidate(work, _load(document_id), index, lease)
                    if terminal is not None:
                        if terminal.outcome is SyncOutcome.ABORTED_STALE:
                            redispatch.append(document_id)
                        else:
                            reports[document_id] = terminal
                        continue
                    terminal, written_outcome, fallback_calls = _apply_plan(
                        work, index, recipe, lease, vectors.get(document_id, ())
                    )
                    calls += fallback_calls
                    if terminal is not None:
                        if terminal.outcome is SyncOutcome.ABORTED_STALE:
                            redispatch.append(document_id)
                        else:
                            reports[document_id] = terminal
                        continue
                    reports[document_id] = _report(
                        work.identity,
                        index,
                        written_outcome,
                        fallback_calls,
                        approved_at=work.approved_at,
                    )
            except DocumentLockUnavailable:
                redispatch.append(document_id)

    redispatch = sorted(set(redispatch))
    emit(
        "retrieval.batch.completed",
        content_type=CONTENT_TYPE,
        document_count=len(ids) + len(over_document_limit),
        processed_count=len(reports),
        redispatched_count=len(redispatch),
        embedding_calls=calls,
        outcomes=dict(
            Counter(
                report_outcome.value
                for report in reports.values()
                if (report_outcome := report.outcome) is not None
            )
        ),
    )
    return BatchSyncReport(
        reports=reports,
        index=index,
        redispatch=tuple(redispatch),
        embedding_calls=calls,
    )


def delete_document_chunks(
    identity: ChunkIdentity, *, target_index: str | None = None
) -> SyncReport:
    """Evict one document from one target under its document lease."""
    index = _resolve_target(target_index)
    if not index:
        return SyncReport(identity)
    with document_lock(identity):
        return _evict(identity, index)
