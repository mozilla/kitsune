"""Deciding, and then performing, what one document needs in one index.

The decision is separated from the work. ``plan_target`` is pure: given what a worker computed
and what an index currently holds, it names an outcome and touches nothing. That keeps the
whole outcome matrix testable without Elasticsearch, Redis, or the database, and leaves the
executor with no judgement of its own to make.
"""

import logging
from dataclasses import dataclass, field
from enum import StrEnum

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
    document_embedding_fingerprint,
    index_state_hash,
)
from kitsune.retrieval.index import (
    ChunkIdentity,
    ChunkSource,
    ExpectedDocumentState,
    IndexedDocumentState,
    delete_chunks_for,
    delete_chunks_for_object,
    read_indexed_document,
    recipe_for_index,
    repair_document_commit,
    replace_chunks,
    resolve_active_targets,
    update_chunks_metadata_for,
)
from kitsune.retrieval.locks import document_lock
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


def _is_usable_vector(vector, recipe: EmbeddingRecipe) -> bool:
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
        and _is_usable_vector(stored.get("content_vector"), recipe)
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
        for position in expected_positions
    ):
        # Scope or source metadata moved while the text did not; rewriting it is free.
        return TargetPlan(SyncOutcome.METADATA_ONLY)

    if orphans or indexed.manifest != expected_state:
        return TargetPlan(SyncOutcome.COMMIT_REPAIR, orphans)

    return TargetPlan(SyncOutcome.NO_OP)


@dataclass(frozen=True)
class SyncReport:
    """What one sync attempt did, per physical index."""

    identity: ChunkIdentity | None
    outcomes: dict[str, SyncOutcome] = field(default_factory=dict)
    # Provider calls actually made, so the cost invariant is observable.
    embedding_calls: int = 0


def _report(
    identity: ChunkIdentity | None,
    outcomes: dict[str, SyncOutcome],
    embedding_calls: int = 0,
    *,
    object_id: str | None = None,
) -> SyncReport:
    """Emit and return one consistent result for every terminal sync path."""
    emit(
        "retrieval.sync.completed",
        content_type=CONTENT_TYPE,
        object_id=identity.object_id if identity else object_id,
        locale=identity.locale if identity else None,
        outcomes={index: outcome.value for index, outcome in outcomes.items()},
        embedding_calls=embedding_calls,
    )
    return SyncReport(identity, outcomes, embedding_calls)


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


def _expected_state(chunks: list[Chunk], source: ChunkSource, document) -> ExpectedDocumentState:
    return ExpectedDocumentState(
        content_hash=content_hash(chunks),
        index_state_hash=index_state_hash(chunks, source),
        chunking_generation=CHUNKING_GENERATION,
        chunk_count=len(chunks),
        indexed_revision_id=document.current_revision_id,
        updated=source.updated,
    )


def _load(document_id: int):
    return (
        Document.objects.filter(pk=document_id)
        .select_related("parent", "current_revision")
        .prefetch_related(
            "products",
            "topics",
            "restrict_to_groups",
            "parent__products",
            "parent__topics",
            "parent__restrict_to_groups",
        )
        .first()
    )


def _resolve_targets(target_indexes) -> tuple[str, ...]:
    """Snapshot the targets once.

    An explicit list is used exactly as supplied, so a backfill pinned to a new generation
    cannot be widened into re-embedding the old one.
    """
    if target_indexes is not None:
        return tuple(target_indexes)
    return resolve_active_targets()


def _evict(
    identity: ChunkIdentity, targets: tuple[str, ...], embedding_calls: int = 0
) -> SyncReport:
    for index in targets:
        delete_chunks_for(index=index, identity=identity)
    return _report(identity, dict.fromkeys(targets, SyncOutcome.DELETED), embedding_calls)


def _evict_object(
    object_id: str, targets: tuple[str, ...], embedding_calls: int = 0
) -> SyncReport:
    """Remove every locale of a source row that no longer exists.

    A deleted row cannot tell us its locale, so the identity-scoped delete is unavailable.
    """
    for index in targets:
        delete_chunks_for_object(index=index, content_type=CONTENT_TYPE, object_id=object_id)
    return _report(
        None,
        dict.fromkeys(targets, SyncOutcome.DELETED),
        embedding_calls,
        object_id=object_id,
    )


def _embed_for_plans(chunks, plans, recipes) -> tuple[dict[str, list[list[float]]], int]:
    """Embed once per distinct vector space rather than once per target.

    Generations sharing an embedding fingerprint share one result; a model migration is the
    case that genuinely needs a call per space.
    """
    vectors_by_fingerprint: dict[str, list[list[float]]] = {}
    vectors_by_index: dict[str, list[list[float]]] = {}
    calls = 0
    for index, plan in plans.items():
        if plan.outcome is not SyncOutcome.EMBED_REPLACE:
            continue
        _, digest = document_embedding_fingerprint(recipes[index])
        if digest not in vectors_by_fingerprint:
            vectors_by_fingerprint[digest] = get_embeddings(
                [item.text for item in chunks], task="document", recipe=recipes[index]
            )
            calls += 1
        vectors_by_index[index] = vectors_by_fingerprint[digest]
    return vectors_by_index, calls


def sync_document_chunks(document_id: int, *, target_indexes=None) -> SyncReport:
    """Bring every target index into agreement with one document, as cheaply as is correct.

    Holds the document's lease for the whole attempt, plans each target independently, embeds
    at most once per vector space, then revalidates the source before writing — because the
    row can change while a provider call is in flight.
    """
    targets = _resolve_targets(target_indexes)
    if not targets:
        emit(
            "retrieval.sync.skipped",
            level=logging.WARNING,
            reason="no_active_index",
            document_id=document_id,
        )
        return SyncReport(None)

    document = _load(document_id)
    if document is None:
        return _evict_object(str(document_id), targets)

    identity = ChunkIdentity(CONTENT_TYPE, str(document.id), document.locale)
    with document_lock(identity) as lease:
        document = _load(document_id)  # authoritative read, now that nobody else may write
        if document is None:
            return _evict_object(identity.object_id, targets)
        if not is_retrieval_indexable(document):
            return _evict(identity, targets)

        source = build_source(document)
        chunks = chunk(CONTENT_TYPE, document.html, title=document.title)
        expected = _expected_state(chunks, source, document)

        # Recipes first: unreadable `_meta` must fail before anything is paid for.
        recipes = {index: recipe_for_index(index) for index in targets}
        plans = {
            index: plan_target(
                chunks=chunks,
                source=source,
                expected_state=expected,
                indexed=read_indexed_document(index=index, identity=identity),
                recipe=recipes[index],
            )
            for index in targets
        }

        # A newer state in any active generation proves this worker is stale. Do not copy
        # that stale state into another generation that happens to be empty.
        if any(plan.outcome is SyncOutcome.ABORTED_STALE for plan in plans.values()):
            return _report(identity, dict.fromkeys(targets, SyncOutcome.ABORTED_STALE))

        outcomes = {index: plan.outcome for index, plan in plans.items()}
        if all(outcome is SyncOutcome.NO_OP for outcome in outcomes.values()):
            return _report(identity, outcomes)

        vectors_by_index, calls = _embed_for_plans(chunks, plans, recipes)

        # Recompute from the reloaded HTML. Included-content rerenders can change HTML without
        # changing current_revision_id, so the revision alone is not a sufficient guard.
        document = _load(document_id)
        if document is None:
            lease.renew()
            return _evict_object(identity.object_id, targets, calls)
        if not is_retrieval_indexable(document):
            lease.renew()
            return _evict(identity, targets, calls)
        fresh_source = build_source(document)
        fresh_chunks = chunk(CONTENT_TYPE, document.html, title=document.title)
        if _expected_state(fresh_chunks, fresh_source, document) != expected:
            return _report(
                identity,
                dict.fromkeys(targets, SyncOutcome.ABORTED_STALE),
                calls,
            )

        for index, plan in plans.items():
            if plan.outcome is SyncOutcome.NO_OP:
                continue

            # A target may need several ES calls. Renew immediately before starting it; the
            # task-level deadline keeps the complete mutation shorter than the lease.
            lease.renew()
            if plan.outcome is SyncOutcome.EMBED_REPLACE:
                replace_chunks(
                    index=index,
                    chunks=chunks,
                    vectors=vectors_by_index[index],
                    source=source,
                    expected_state=expected,
                )
            elif plan.outcome is SyncOutcome.METADATA_ONLY:
                update_chunks_metadata_for(
                    index=index,
                    chunks=chunks,
                    source=source,
                    expected_state=expected,
                )
            elif plan.outcome is SyncOutcome.COMMIT_REPAIR:
                repair_document_commit(
                    index=index,
                    identity=identity,
                    expected_state=expected,
                    orphan_positions=plan.orphan_positions,
                )

    return _report(identity, outcomes, calls)


def delete_document_chunks(identity: ChunkIdentity, *, target_indexes=None) -> SyncReport:
    """Evict one document from every target, under its lease so no sync races the removal."""
    targets = _resolve_targets(target_indexes)
    if not targets:
        return SyncReport(identity)
    with document_lock(identity):
        return _evict(identity, targets)
