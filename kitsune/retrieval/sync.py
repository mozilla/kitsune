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
    IndexedDocumentState,
    access_metadata_matches,
    delete_chunks_for,
    delete_chunks_for_object,
    read_indexed_document,
    recipe_for_index,
    repair_document_commit,
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
    COMMIT_REPAIR = "commit_repair"
    NO_OP = "no_op"
    DELETED = "deleted"
    ABORTED_STALE = "aborted_stale"


@dataclass(frozen=True)
class TargetPlan:
    outcome: SyncOutcome
    # Only a commit repair needs these: the other write paths derive orphans from the
    # expected positions themselves.
    orphan_positions: tuple[int, ...] = ()


def _is_newer(stored: int | None, proposed: int) -> bool:
    return isinstance(stored, int) and not isinstance(stored, bool) and stored > proposed


def _stored_is_newer(indexed: IndexedDocumentState, expected: ExpectedDocumentState) -> bool:
    """Whether the index already holds output this worker would be downgrading.

    Checks the chunks as well as the manifest, because a crash can leave newer chunks behind
    with no manifest to describe them.
    """
    manifest = indexed.manifest
    if manifest and (
        _is_newer(manifest.chunking_generation, expected.chunking_generation)
        or _is_newer(manifest.indexed_revision_id, expected.indexed_revision_id)
    ):
        return True
    return any(
        _is_newer(chunk.get("chunking_generation"), expected.chunking_generation)
        for chunk in indexed.chunks
    )


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


def _is_recoverable(
    stored: dict | None,
    chunk: Chunk,
    source: ChunkSource,
    expected: ExpectedDocumentState,
    recipe: EmbeddingRecipe,
) -> bool:
    """Whether this position can be kept as-is instead of being re-embedded.

    The text and vector have to be exactly what the expected chunk implies, because a
    metadata-only update rewrites neither of them.
    """
    if stored is None:
        return False
    stored_text = stored.get("content_text")
    return (
        isinstance(stored_text, dict)
        and stored_text.get(source.locale) == chunk.text
        and stored.get("content_hash") == expected.content_hash
        and stored.get("chunking_generation") == expected.chunking_generation
        and is_usable_vector(stored.get("content_vector"), recipe)
    )


def plan_target(
    *,
    chunks: list[Chunk],
    source: ChunkSource,
    expected_state: ExpectedDocumentState,
    indexed: IndexedDocumentState,
    recipe: EmbeddingRecipe,
) -> TargetPlan:
    """Name the cheapest outcome that makes this index correct for this document.

    Ordered cheapest-last on purpose: staleness is decided before anything else so a worker
    holding older content aborts without paying the provider, and the metadata path is
    preferred over re-embedding whenever the stored text and vectors are still trustworthy.
    """
    if _stored_is_newer(indexed, expected_state):
        return TargetPlan(SyncOutcome.ABORTED_STALE)

    by_position = {chunk["position"]: chunk for chunk in indexed.chunks}
    expected_positions = range(len(chunks))
    orphans = tuple(sorted(set(by_position) - set(expected_positions)))

    if not all(
        _is_recoverable(by_position.get(chunk.position), chunk, source, expected_state, recipe)
        for chunk in chunks
    ):
        return TargetPlan(SyncOutcome.EMBED_REPLACE)

    if any(
        by_position[position].get("index_state_hash") != expected_state.index_state_hash
        or not access_metadata_matches(by_position[position], source)
        for position in expected_positions
    ):
        # Scope or source metadata moved while the text did not; rewriting it is free.
        return TargetPlan(SyncOutcome.METADATA_ONLY)

    if orphans or indexed.manifest != expected_state:
        return TargetPlan(SyncOutcome.COMMIT_REPAIR, orphans)

    return TargetPlan(SyncOutcome.NO_OP)


@dataclass(frozen=True)
class SyncReport:
    """What one single-target sync attempt did."""

    identity: ChunkIdentity | None
    index: str | None = None
    outcome: SyncOutcome | None = None
    # Embedding-adapter calls actually made. Zero inside a batch, where a shared call belongs
    # to the batch rather than to any one document.
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

    identity: ChunkIdentity
    source: ChunkSource
    chunks: list[Chunk]
    expected: ExpectedDocumentState
    plan: TargetPlan
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
        if work.plan.outcome is SyncOutcome.EMBED_REPLACE:
            spans[document_id] = (len(inputs), len(inputs) + len(work.chunks))
            inputs.extend(chunk.text for chunk in work.chunks)

    if not inputs:
        return {}, 0
    combined = get_embeddings(inputs, task="document", recipe=recipe)
    return {document_id: combined[start:stop] for document_id, (start, stop) in spans.items()}, 1


def _plan_document(document, index, recipe) -> _DocumentWork | SyncReport:
    """Plan one locked, eligible document for one index—or finish it outright.

    Returns a report when the document needs no provider work: it is stale or already agrees
    with the target.
    """
    identity = _identity_for(document)
    source = build_source(document)
    chunks = chunk(CONTENT_TYPE, document.html, title=document.title)
    expected = expected_state_for(chunks, source, document)
    plan = plan_target(
        chunks=chunks,
        source=source,
        expected_state=expected,
        indexed=read_indexed_document(index=index, identity=identity),
        recipe=recipe,
    )

    if plan.outcome is SyncOutcome.ABORTED_STALE:
        return _report(identity, index, SyncOutcome.ABORTED_STALE)

    work = _DocumentWork(
        identity, source, chunks, expected, plan, document.current_revision.reviewed
    )
    if plan.outcome is SyncOutcome.NO_OP:
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


def _write_plan(work: _DocumentWork, index: str, lease, vectors=()) -> None:
    # A plan may need several ES calls. Renew immediately before starting it; the task-level
    # deadline keeps the complete mutation shorter than the lease.
    lease.renew()
    if work.plan.outcome is SyncOutcome.EMBED_REPLACE:
        replace_chunks(
            index=index,
            chunks=work.chunks,
            vectors=vectors,
            source=work.source,
            expected_state=work.expected,
        )
    elif work.plan.outcome is SyncOutcome.METADATA_ONLY:
        update_chunks_metadata_for(
            index=index,
            chunks=work.chunks,
            source=work.source,
            expected_state=work.expected,
        )
    elif work.plan.outcome is SyncOutcome.COMMIT_REPAIR:
        repair_document_commit(
            index=index,
            identity=work.identity,
            expected_state=work.expected,
            orphan_positions=work.plan.orphan_positions,
        )


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
        work = _plan_document(document, index, recipe)
        if isinstance(work, SyncReport):
            return work

        vectors, calls = _embed_for_works({document_id: work}, recipe)
        terminal = _revalidate(work, _load(document_id), index, lease, calls)
        if terminal is not None:
            return terminal
        _write_plan(work, index, lease, vectors.get(document_id, ()))

    return _report(identity, index, work.plan.outcome, calls, approved_at=work.approved_at)


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
        needed = len(work.chunks) if work.plan.outcome is SyncOutcome.EMBED_REPLACE else 0
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
        recipe = recipe_for_index(index) if eligible else None
        works: dict[int, _DocumentWork] = {}
        for document_id, document in eligible.items():
            planned = _plan_document(document, index, recipe)
            if isinstance(planned, SyncReport):
                reports[document_id] = planned
            else:
                works[document_id] = planned

        works, over_input_limit = _within_input_budget(works, max_inputs)
        for document_id in over_input_limit:
            # Nothing will be written for it, so stop holding it for the rest of the batch.
            leases[document_id].release()

        vectors, calls = _embed_for_works(works, recipe) if recipe else ({}, 0)

        fresh = _load_many(works)
        for document_id, work in works.items():
            lease = leases[document_id]
            try:
                terminal = _revalidate(work, fresh.get(document_id), index, lease)
                if terminal is not None:
                    reports[document_id] = terminal
                    continue
                _write_plan(work, index, lease, vectors.get(document_id, ()))
            except DocumentLockUnavailable:
                # One stolen lease is that document's problem; the rest of the batch stands.
                contended.append(document_id)
                continue
            reports[document_id] = _report(
                work.identity,
                index,
                work.plan.outcome,
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
                outcome.value
                for report in reports.values()
                if (outcome := report.outcome) is not None
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
