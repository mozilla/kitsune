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
from contextlib import ExitStack
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
    InvalidEmbeddingResponse,
    get_embeddings,
    validate_embeddings,
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


def is_usable_vector(vector, recipe: EmbeddingRecipe) -> bool:
    """Whether a stored vector is one this recipe would have written.

    Public so the integrity gate applies the writer's own definition rather than a second one
    that could pass a vector the writer would reject.
    """
    if not isinstance(vector, list):
        return False
    try:
        validate_embeddings([vector], ["stored chunk"], recipe)
    except InvalidEmbeddingResponse:
        return False
    return True


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
    if manifest and (
        manifest.chunking_generation > expected_state.chunking_generation
        or manifest.indexed_revision_id > expected_state.indexed_revision_id
    ):
        return SyncOutcome.ABORTED_STALE

    if manifest is None or manifest.content_hash != expected_state.content_hash:
        return SyncOutcome.EMBED_REPLACE

    positions = {summary.position for summary in summaries}
    if len(summaries) != len(chunks) or positions != set(range(len(chunks))):
        return SyncOutcome.EMBED_REPLACE

    access_matches = all(
        summary.visibility == source.visibility
        and summary.access_group_ids == source.access_group_ids
        for summary in summaries
    )
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
    """What one batch attempt did. Contended and deferred documents are unfinished work."""

    reports: dict[int, SyncReport] = field(default_factory=dict)
    contended: tuple[int, ...] = ()
    deferred: tuple[int, ...] = ()
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

    Public for the same reason as ``is_usable_vector``: the gate has to compare against exactly
    what the writer would have produced.
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


def _within_input_budget(
    works: dict[int, _DocumentWork], max_inputs: int
) -> tuple[dict[int, _DocumentWork], tuple[int, ...]]:
    """Trim the batch to the configured embedding-input bound.

    The first document is always admitted, whatever it costs: an article with more chunks than
    the bound would otherwise be deferred out of every batch forever.
    """
    admitted: dict[int, _DocumentWork] = {}
    deferred: list[int] = []
    used = 0
    for document_id, work in works.items():
        needed = len(work.chunks) if work.outcome is SyncOutcome.EMBED_REPLACE else 0
        if admitted and used + needed > max_inputs:
            deferred.append(document_id)
            continue
        admitted[document_id] = work
        used += needed
    return admitted, tuple(deferred)


def sync_document_batch(document_ids, *, target_index: str | None = None) -> BatchSyncReport:
    """Bring documents into agreement with one target, sharing the provider call.

    Per-document correctness is unchanged: each document is planned, revalidated, and committed
    under its own lease, and holds that lease across its own writes. Only the embedding calls
    are shared. A document another worker is already holding is reported rather than waited on,
    so one contended document cannot stall the batch.
    """
    ids = ordered_document_ids(document_ids)
    if not ids:
        return BatchSyncReport()

    max_documents = max_batch_documents()
    max_inputs = _bulk_bound("RETRIEVAL_BULK_MAX_EMBEDDING_INPUTS")
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
    contended: list[int] = []

    with ExitStack() as stack:
        leases = {}
        known = _load_many(ids)
        for document_id in ids:
            document = known.get(document_id)
            if document is None:
                reports[document_id] = _evict_object(str(document_id), index)
                continue
            try:
                leases[document_id] = stack.enter_context(document_lock(_identity_for(document)))
            except DocumentLockUnavailable:
                contended.append(document_id)

        eligible = {}
        locked = _load_many(leases)  # authoritative read, now that nobody else may write
        for document_id in leases:
            document = locked.get(document_id)
            if document is None:
                reports[document_id] = _evict_object(str(document_id), index)
            elif not is_retrieval_indexable(document):
                reports[document_id] = _evict(_identity_for(document), index)
            else:
                eligible[document_id] = document

        # Invalid target metadata must not prevent the safety evictions above. It still fails
        # before any provider call or indexing write for eligible documents.
        calls = 0
        over_input_limit: tuple[int, ...] = ()
        if eligible:
            recipe = recipe_for_index(index)
            works: dict[int, _DocumentWork] = {}
            for document_id, document in eligible.items():
                planned = _plan_document(document, index)
                if isinstance(planned, SyncReport):
                    reports[document_id] = planned
                else:
                    works[document_id] = planned

            works, over_input_limit = _within_input_budget(works, max_inputs)
            for document_id in over_input_limit:
                # Nothing will be written for it, so stop holding it for the rest of the batch.
                leases[document_id].release()

            vectors, calls = _embed_for_works(works, recipe)
            fresh = _load_many(works)
            for document_id, work in works.items():
                lease = leases[document_id]
                try:
                    terminal = _revalidate(work, fresh.get(document_id), index, lease)
                    if terminal is not None:
                        reports[document_id] = terminal
                        continue
                    terminal, written_outcome, fallback_calls = _apply_plan(
                        work, index, recipe, lease, vectors.get(document_id, ())
                    )
                    calls += fallback_calls
                    if terminal is not None:
                        reports[document_id] = terminal
                        continue
                except DocumentLockUnavailable:
                    # One stolen lease is that document's problem; the rest of the batch stands.
                    contended.append(document_id)
                    continue
                reports[document_id] = _report(
                    work.identity,
                    index,
                    written_outcome,
                    fallback_calls,
                    approved_at=work.approved_at,
                )

    deferred = tuple(sorted(over_document_limit + over_input_limit))
    if deferred:
        emit(
            "retrieval.batch.deferred",
            level=logging.WARNING,
            over_document_limit=len(over_document_limit),
            over_input_limit=len(over_input_limit),
            document_ids=",".join(str(document_id) for document_id in deferred),
        )
    emit(
        "retrieval.batch.completed",
        content_type=CONTENT_TYPE,
        document_count=len(ids) + len(over_document_limit),
        synced=len(reports),
        contended_count=len(contended),
        deferred_count=len(deferred),
        embedding_calls=calls,
        outcomes=dict(
            Counter(
                report_outcome.value
                for report in reports.values()
                if (report_outcome := report.outcome) is not None
            )
        ),
    )
    return BatchSyncReport(reports, tuple(sorted(contended)), deferred, calls)


def delete_document_chunks(
    identity: ChunkIdentity, *, target_index: str | None = None
) -> SyncReport:
    """Evict one document from one target under its document lease."""
    index = _resolve_target(target_index)
    if not index:
        return SyncReport(identity)
    with document_lock(identity):
        return _evict(identity, index)
