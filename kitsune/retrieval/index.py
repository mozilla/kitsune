import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar

from django.conf import settings
from elasticsearch import NotFoundError
from elasticsearch.dsl import field
from elasticsearch.dsl.types import DenseVectorIndexOptions
from elasticsearch.helpers import bulk, scan

from kitsune.retrieval.chunking import Chunk
from kitsune.retrieval.embeddings import (
    EmbeddingRecipe,
    configured_embedding_recipe,
    recipe_from_payload,
)
from kitsune.retrieval.fingerprints import (
    InvalidIndexMeta,
    build_index_meta,
    content_hash,
    index_state_hash,
    mapping_fingerprint,
    read_index_meta,
    scope_envelope,
    write_index_meta,
)
from kitsune.search.base import SumoDocument
from kitsune.search.es_utils import es_client
from kitsune.search.fields import SumoLocaleAwareKeywordField, SumoLocaleAwareTextField

# Single source of truth for the vector dimensionality, shared with the embedding recipe
# (settings.RETRIEVAL_EMBEDDING_DIMENSIONS) so the mapping and the vectors can't disagree.
VECTOR_DIMS = settings.RETRIEVAL_EMBEDDING_DIMENSIONS
# Vector-mapping properties, shared by the mapping and its fingerprint so they can't drift.
SIMILARITY = "cosine"
VECTOR_INDEX_OPTIONS = {"type": "hnsw", "m": 16, "ef_construction": 100}
# Bump when an index-time mapping change requires a new physical index while allowing
# existing vectors to be copied.
SCHEMA_VERSION = 1

CHUNK_KIND = "chunk"
MANIFEST_KIND = "manifest"
PUBLIC_VISIBILITY = "public"
RESTRICTED_VISIBILITY = "group_restricted"
_ID_DELIMITER = ":"
_SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")
_MANIFEST_SOURCE_FIELDS = frozenset(
    {
        "kind",
        "content_type",
        "object_id",
        "locale",
        "content_hash",
        "index_state_hash",
        "chunk_count",
        "chunking_generation",
        "indexed_revision_id",
        "updated",
    }
)


class InvalidDocumentState(ValueError):
    """A retrieval identity, source, manifest, or expected state is malformed."""


def _require_string(value, name: str, *, nonempty: bool = False) -> None:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        qualifier = "non-empty " if nonempty else ""
        raise InvalidDocumentState(f"{name} must be a {qualifier}string")


def _require_identity_component(value, name: str) -> None:
    _require_string(value, name, nonempty=True)
    if _ID_DELIMITER in value:
        raise InvalidDocumentState(f"{name} must not contain {_ID_DELIMITER!r}")


def _require_int(value, name: str, *, minimum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise InvalidDocumentState(f"{name} must be an integer >= {minimum}")


def _require_aware_datetime(value, name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise InvalidDocumentState(f"{name} must be a timezone-aware datetime")


def _canonical_string_ids(values, name: str) -> tuple[str, ...]:
    if isinstance(values, str | bytes):
        raise InvalidDocumentState(f"{name} must be a sequence of strings")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise InvalidDocumentState(f"{name} must be a sequence of strings") from exc
    for value in items:
        _require_string(value, f"{name} item", nonempty=True)
    if len(set(items)) != len(items):
        raise InvalidDocumentState(f"{name} must not contain duplicates")
    return tuple(sorted(items))


def _int_items(values, name: str, *, minimum: int) -> tuple[int, ...]:
    if isinstance(values, str | bytes):
        raise InvalidDocumentState(f"{name} must be a sequence of integers")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise InvalidDocumentState(f"{name} must be a sequence of integers") from exc
    for value in items:
        _require_int(value, f"{name} item", minimum=minimum)
    return items


def _canonical_positions(values) -> tuple[int, ...]:
    # A position set: repeats carry no meaning, so they collapse rather than fail.
    return tuple(sorted(set(_int_items(values, "orphan_positions", minimum=0))))


def _canonical_group_ids(values) -> tuple[int, ...]:
    items = _int_items(values, "access_group_ids", minimum=1)
    if len(set(items)) != len(items):
        raise InvalidDocumentState("access_group_ids must not contain duplicates")
    return tuple(sorted(items))


class ChunkDocument(SumoDocument):
    """One physical index holds two `kind`s: per-passage ``chunk`` docs and one
    ``manifest`` commit marker per source document. The mapping is their union; each doc
    only populates the fields for its kind."""

    kind = field.Keyword()

    # chunk payload
    content_text = SumoLocaleAwareTextField()
    content_vector = field.DenseVector(
        dims=VECTOR_DIMS,
        similarity=SIMILARITY,
        index=True,
        index_options=DenseVectorIndexOptions(**VECTOR_INDEX_OPTIONS),
    )
    scope = field.Object(enabled=False)  # lossless, opaque; stored in _source only
    scope_clause_count = field.Integer()
    applies_to = field.Keyword(multi=True)  # lossy flattened union; coarse selection only
    heading_path = field.Text()
    position = field.Integer()

    # identity fields (content_type/object_id/locale are shared by both kinds)
    content_type = field.Keyword()
    object_id = field.Keyword()
    # family/access metadata is chunk-only
    family_id = field.Keyword()
    locale = field.Keyword()
    visibility = field.Keyword()
    access_group_ids = field.Keyword(multi=True)

    # per-document state (repeated on chunks for recovery; authoritative on the manifest)
    content_hash = field.Keyword()
    index_state_hash = field.Keyword()
    chunking_generation = field.Integer()

    # manifest-only state
    chunk_count = field.Integer()
    indexed_revision_id = field.Long()

    # denormalized source metadata
    title = SumoLocaleAwareTextField()
    summary = SumoLocaleAwareTextField()
    keywords = SumoLocaleAwareTextField()
    slug = SumoLocaleAwareKeywordField()
    category = field.Keyword()
    product_ids = field.Keyword(multi=True)
    topic_ids = field.Keyword(multi=True)
    updated = field.Date()

    class Index:
        # populated at runtime by SumoDocument.__init_subclass__
        base_name: ClassVar[str]
        read_alias: ClassVar[str]
        write_alias: ClassVar[str]


@dataclass(frozen=True)
class ChunkIdentity:
    """The identity a set of chunks and their manifest share within one index."""

    content_type: str
    object_id: str
    locale: str

    def __post_init__(self):
        _require_identity_component(self.content_type, "content_type")
        _require_identity_component(self.object_id, "object_id")
        _require_identity_component(self.locale, "locale")


@dataclass(frozen=True)
class ChunkSource:
    """Identity, family, and denormalized source metadata shared across a document's chunks.

    Structurally satisfies ``fingerprints.ChunkStateSource``. Hashes are computed from
    chunks and source metadata, never supplied by callers, so this carries no hash fields.
    """

    content_type: str
    object_id: str
    locale: str
    family_id: str
    title: str
    summary: str
    keywords: str
    slug: str
    category: str
    product_ids: tuple[str, ...]
    topic_ids: tuple[str, ...]
    visibility: str
    access_group_ids: tuple[int, ...]
    updated: datetime

    def __post_init__(self):
        # Validate the three ID components and the delimiter contract once at construction.
        self.identity
        _require_string(self.family_id, "family_id", nonempty=True)
        for name in ("title", "summary", "keywords", "slug", "category"):
            _require_string(getattr(self, name), name)
        _require_aware_datetime(self.updated, "updated")

        product_ids = _canonical_string_ids(self.product_ids, "product_ids")
        topic_ids = _canonical_string_ids(self.topic_ids, "topic_ids")
        access_group_ids = _canonical_group_ids(self.access_group_ids)
        object.__setattr__(self, "product_ids", product_ids)
        object.__setattr__(self, "topic_ids", topic_ids)
        object.__setattr__(self, "access_group_ids", access_group_ids)

        if self.visibility == PUBLIC_VISIBILITY:
            if access_group_ids:
                raise InvalidDocumentState("public visibility requires empty access_group_ids")
        elif self.visibility == RESTRICTED_VISIBILITY:
            if not access_group_ids:
                raise InvalidDocumentState("group_restricted visibility requires access_group_ids")
        else:
            raise InvalidDocumentState("visibility must be 'public' or 'group_restricted'")

    @property
    def identity(self) -> ChunkIdentity:
        return ChunkIdentity(self.content_type, self.object_id, self.locale)


@dataclass(frozen=True)
class ExpectedDocumentState:
    """One worker-computed expected commit, stored authoritatively on the manifest."""

    content_hash: str
    index_state_hash: str
    chunking_generation: int
    chunk_count: int
    indexed_revision_id: int
    updated: datetime

    def __post_init__(self):
        for name in ("content_hash", "index_state_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or not _SHA256_HEX.fullmatch(value):
                raise InvalidDocumentState(f"{name} must be a SHA-256 hex digest")
        _require_int(self.chunking_generation, "chunking_generation", minimum=1)
        _require_int(self.chunk_count, "chunk_count", minimum=0)
        _require_int(self.indexed_revision_id, "indexed_revision_id", minimum=1)
        _require_aware_datetime(self.updated, "updated")


def chunk_id(identity: ChunkIdentity, position: int) -> str:
    _require_int(position, "position", minimum=0)
    return f"{identity.content_type}:{identity.object_id}:{identity.locale}:{position}"


def manifest_id(identity: ChunkIdentity) -> str:
    return f"{identity.content_type}:{identity.object_id}:{identity.locale}:manifest"


def manifest_doc(identity: ChunkIdentity, state: ExpectedDocumentState) -> ChunkDocument:
    """Build the manifest commit marker for a document (kind=``manifest``, no vector/text)."""
    doc = ChunkDocument(
        kind=MANIFEST_KIND,
        content_type=identity.content_type,
        object_id=identity.object_id,
        locale=identity.locale,
        content_hash=state.content_hash,
        index_state_hash=state.index_state_hash,
        chunk_count=state.chunk_count,
        chunking_generation=state.chunking_generation,
        indexed_revision_id=state.indexed_revision_id,
        updated=state.updated,
    )
    doc.meta.id = manifest_id(identity)
    return doc


def parse_manifest(source: Mapping) -> ExpectedDocumentState:
    """Validate and reconstruct expected state from a manifest ``_source``."""
    if not isinstance(source, Mapping):
        raise InvalidDocumentState("manifest _source must be an object")
    if set(source) != _MANIFEST_SOURCE_FIELDS:
        raise InvalidDocumentState(
            f"manifest _source must contain exactly {sorted(_MANIFEST_SOURCE_FIELDS)!r}"
        )
    if source["kind"] != MANIFEST_KIND:
        raise InvalidDocumentState("manifest _source kind must be 'manifest'")
    ChunkIdentity(
        content_type=source["content_type"],
        object_id=source["object_id"],
        locale=source["locale"],
    )

    updated = source["updated"]
    if isinstance(updated, str):
        try:
            updated = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except ValueError as exc:
            raise InvalidDocumentState("manifest updated is not a valid timestamp") from exc
    return ExpectedDocumentState(
        content_hash=source["content_hash"],
        index_state_hash=source["index_state_hash"],
        chunking_generation=source["chunking_generation"],
        chunk_count=source["chunk_count"],
        indexed_revision_id=source["indexed_revision_id"],
        updated=updated,
    )


@dataclass(frozen=True)
class IndexedDocumentState:
    """What one concrete index holds for a document: its manifest (``None`` when missing)
    and its chunk ``_source`` dicts, sorted by position."""

    manifest: ExpectedDocumentState | None
    chunks: list[dict]


class IndexWriteError(Exception):
    """An Elasticsearch write or delete did not fully succeed."""


def _require_concrete_index(index: str) -> None:
    _require_string(index, "index", nonempty=True)
    pattern = rf"{re.escape(ChunkDocument.Index.base_name)}_[0-9]{{14}}"
    if not re.fullmatch(pattern, index):
        raise InvalidDocumentState(
            f"{index!r} is not a concrete {ChunkDocument.Index.base_name!r} generation"
        )


def _identity_filters(identity: ChunkIdentity) -> list[dict]:
    return [
        {"term": {"content_type": identity.content_type}},
        {"term": {"object_id": identity.object_id}},
        {"term": {"locale": identity.locale}},
    ]


def _verify_expected_state(
    chunks: list[Chunk], source: ChunkSource, expected_state: ExpectedDocumentState
) -> None:
    """Prove the expected commit was derived from exactly these chunks and this source."""
    if [chunk.position for chunk in chunks] != list(range(len(chunks))):
        raise InvalidDocumentState("chunk positions must be contiguous and start at zero")
    if expected_state.chunk_count != len(chunks):
        raise InvalidDocumentState("expected_state.chunk_count must equal the number of chunks")
    if expected_state.content_hash != content_hash(chunks):
        raise InvalidDocumentState("expected_state.content_hash does not match the chunks")
    if expected_state.index_state_hash != index_state_hash(chunks, source):
        raise InvalidDocumentState(
            "expected_state.index_state_hash does not match the chunks and source"
        )
    if expected_state.updated != source.updated:
        raise InvalidDocumentState("expected_state.updated does not match the source")


def _chunk_metadata(
    chunk: Chunk, source: ChunkSource, expected_state: ExpectedDocumentState
) -> dict:
    """Every per-chunk field a metadata-only update owns.

    Shared by the full write and the metadata-only update so the two cannot drift into
    disagreeing about what a chunk's recovery state should look like. Deliberately excluded:
    ``kind``, ``content_type``, ``object_id``, ``locale`` and ``position`` (they identify the
    document, and changing one means a different chunk), ``content_text``/``content_vector``
    (only a re-embed may rewrite those), and ``indexed_on``, which keeps meaning "when this
    chunk's text and vector were written" rather than "last touched".
    """
    locale = source.locale
    return {
        "heading_path": chunk.heading_path,
        "applies_to": sorted(chunk.applies_to),
        "scope": scope_envelope(chunk.scope),
        "scope_clause_count": len(chunk.scope),
        "family_id": source.family_id,
        "visibility": source.visibility,
        "access_group_ids": list(source.access_group_ids),
        "content_hash": expected_state.content_hash,
        "index_state_hash": expected_state.index_state_hash,
        "chunking_generation": expected_state.chunking_generation,
        "title": {locale: source.title},
        "summary": {locale: source.summary},
        "keywords": {locale: source.keywords},
        "slug": {locale: source.slug},
        "category": source.category,
        "product_ids": list(source.product_ids),
        "topic_ids": list(source.topic_ids),
        "updated": source.updated,
    }


def write_chunks(
    *,
    index: str,
    chunks: list[Chunk],
    vectors: list[list[float]],
    source: ChunkSource,
    expected_state: ExpectedDocumentState,
) -> None:
    """Bulk-write and verify one chunk document per chunk to a concrete index. Vectors are
    supplied by the caller — the write path never calls the embedding adapter."""
    _require_concrete_index(index)
    if len(vectors) != len(chunks):
        raise InvalidDocumentState("write_chunks requires exactly one vector per chunk")
    _verify_expected_state(chunks, source, expected_state)

    locale = source.locale
    identity = source.identity
    indexed_on = datetime.now(tz=UTC)
    actions = []
    for chunk, vector in zip(chunks, vectors, strict=True):
        doc = ChunkDocument(
            kind=CHUNK_KIND,
            content_text={locale: chunk.text},
            content_vector=list(vector),
            content_type=source.content_type,
            object_id=source.object_id,
            locale=locale,
            position=chunk.position,
            indexed_on=indexed_on,
            **_chunk_metadata(chunk, source, expected_state),
        )
        doc.meta.id = chunk_id(identity, chunk.position)
        action = doc.to_action(action="index", is_bulk=True)
        action["_index"] = index  # target the concrete generation, never the alias default
        actions.append(action)

    _verified_bulk(actions)


def commit_manifest(
    *, index: str, identity: ChunkIdentity, expected_state: ExpectedDocumentState
) -> None:
    """Write the per-document manifest as the final commit marker."""
    _require_concrete_index(index)
    doc = manifest_doc(identity, expected_state)
    result = es_client().index(
        index=index, id=manifest_id(identity), document=doc.to_dict(), refresh=settings.TEST
    )
    if result.get("result") not in ("created", "updated"):
        raise IndexWriteError(f"manifest commit for {manifest_id(identity)} returned {result!r}")


def delete_orphan_chunks(
    *, index: str, identity: ChunkIdentity, expected_positions: range | set[int]
) -> None:
    """Delete this document's chunk docs whose position is not in ``expected_positions``
    (positions left over from a larger previous generation). The manifest is untouched."""
    _require_concrete_index(index)
    _verified_delete_by_query(
        index,
        {
            "bool": {
                "filter": [*_identity_filters(identity), {"term": {"kind": CHUNK_KIND}}],
                "must_not": [{"terms": {"position": sorted(expected_positions)}}],
            }
        },
    )


def delete_chunk_positions(
    *, index: str, identity: ChunkIdentity, positions: range | set[int] | tuple[int, ...]
) -> None:
    """Delete only the named chunk positions. The manifest is untouched.

    The complement of ``delete_orphan_chunks``: naming the doomed positions instead of the
    surviving ones keeps a caller working from a stale view of the document from evicting
    chunks it never saw.
    """
    _require_concrete_index(index)
    _verified_delete_by_query(
        index,
        {
            "bool": {
                "filter": [
                    *_identity_filters(identity),
                    {"term": {"kind": CHUNK_KIND}},
                    {"terms": {"position": sorted(positions)}},
                ]
            }
        },
    )


def replace_chunks(
    *,
    index: str,
    chunks: list[Chunk],
    vectors: list[list[float]],
    source: ChunkSource,
    expected_state: ExpectedDocumentState,
) -> None:
    """Write and verify chunks, delete and verify orphans, then commit the manifest.

    A crash before the final marker leaves the document detectably incomplete and safe to
    replay. Writing replacements before deleting orphans avoids a zero-chunk window.
    """
    _require_concrete_index(index)
    write_chunks(
        index=index, chunks=chunks, vectors=vectors, source=source, expected_state=expected_state
    )
    delete_orphan_chunks(
        index=index, identity=source.identity, expected_positions=range(len(chunks))
    )
    commit_manifest(index=index, identity=source.identity, expected_state=expected_state)


def update_chunks_metadata_for(
    *,
    index: str,
    chunks: list[Chunk],
    source: ChunkSource,
    expected_state: ExpectedDocumentState,
) -> None:
    """Rewrite each existing position's metadata and state in place, delete orphans, commit.

    The cheapest correct path when only scope or source metadata changed: it preserves each
    chunk's stored text and vector and makes no embedding call. The caller must already have
    verified that every expected position's stored text, vector, and content hash are correct
    — this never creates a missing position, because a chunk without text and a vector would
    be indistinguishable from a real one.

    While ingestion is public-only, an access change never reaches here: it flips the
    document's eligibility, so the sync core evicts it or indexes it afresh instead. Once
    restricted ingestion is enabled, a change to `visibility`/`access_group_ids` becomes an
    ordinary metadata change and this is the path it takes (ADR 0006).
    """
    _require_concrete_index(index)
    _verify_expected_state(chunks, source, expected_state)

    identity = source.identity
    actions = []
    for chunk in chunks:
        doc = ChunkDocument(**_chunk_metadata(chunk, source, expected_state))
        doc.meta.id = chunk_id(identity, chunk.position)
        # Partial doc + no doc_as_upsert: text/vector are absent from the payload so they
        # survive the merge, and a missing position fails instead of being created.
        action = doc.to_action(action="update", is_bulk=True)
        action["_index"] = index
        actions.append(action)

    _verified_bulk(actions)
    delete_orphan_chunks(index=index, identity=identity, expected_positions=range(len(chunks)))
    commit_manifest(index=index, identity=identity, expected_state=expected_state)


def repair_document_commit(
    *,
    index: str,
    identity: ChunkIdentity,
    expected_state: ExpectedDocumentState,
    orphan_positions,
) -> None:
    """Delete an enumerated set of leftover positions, then commit the manifest.

    The narrow recovery for a crash between verified chunk writes and their manifest: it
    writes no chunk content and makes no embedding call. Legal only once the caller has
    validated every expected position's text, vector, hash, and state. Deleting an explicit
    list rather than everything unexpected keeps a stale caller from evicting live chunks.
    """
    _require_concrete_index(index)
    orphans = _canonical_positions(orphan_positions)
    conflicting = sorted(set(orphans) & set(range(expected_state.chunk_count)))
    if conflicting:
        raise InvalidDocumentState(
            f"orphan positions {conflicting!r} are expected by the manifest being committed"
        )

    if orphans:
        delete_chunk_positions(index=index, identity=identity, positions=orphans)
    commit_manifest(index=index, identity=identity, expected_state=expected_state)


def read_indexed_document(*, index: str, identity: ChunkIdentity) -> IndexedDocumentState:
    """Read a document's manifest and every one of its chunks (scanned, then sorted by
    position — never limited to Elasticsearch's default page)."""
    _require_concrete_index(index)
    return IndexedDocumentState(
        manifest=_read_manifest(index, identity),
        chunks=_read_chunks(index, identity),
    )


def _read_manifest(index: str, identity: ChunkIdentity) -> ExpectedDocumentState | None:
    try:
        response = es_client().get(index=index, id=manifest_id(identity))
    except NotFoundError:
        return None
    source = response["_source"]
    state = parse_manifest(source)
    stored_identity = ChunkIdentity(
        content_type=source["content_type"],
        object_id=source["object_id"],
        locale=source["locale"],
    )
    if stored_identity != identity:
        raise InvalidDocumentState(
            f"manifest {manifest_id(identity)!r} contains identity {stored_identity!r}"
        )
    return state


def _read_chunks(index: str, identity: ChunkIdentity) -> list[dict]:
    body = {
        "query": {
            "bool": {"filter": [*_identity_filters(identity), {"term": {"kind": CHUNK_KIND}}]}
        },
        # dense_vector is excluded from _source by default in ES 9.x; opt it back in so the
        # sync core can verify each chunk's stored vector.
        "_source": {"exclude_vectors": False},
    }
    hits = scan(es_client(), index=index, query=body)
    return sorted((hit["_source"] for hit in hits), key=lambda chunk: chunk["position"])


def delete_chunks_for(*, index: str, identity: ChunkIdentity) -> None:
    """Remove a document's chunks and manifest from one concrete index."""
    _require_concrete_index(index)
    _verified_delete_by_query(index, {"bool": {"filter": _identity_filters(identity)}})


def delete_chunks_for_object(*, index: str, content_type: str, object_id: str) -> None:
    """Missing-locale fallback: remove every locale's chunks and manifests for an object,
    used when a delayed deletion cannot recover the locale from the vanished source row."""
    _require_concrete_index(index)
    _require_identity_component(content_type, "content_type")
    _require_identity_component(object_id, "object_id")
    _verified_delete_by_query(
        index,
        {
            "bool": {
                "filter": [
                    {"term": {"content_type": content_type}},
                    {"term": {"object_id": object_id}},
                ]
            }
        },
    )


def _verified_bulk(actions: list[dict]) -> None:
    if not actions:
        return
    succeeded, errors = bulk(
        es_client(),
        actions,
        raise_on_error=False,
        chunk_size=settings.ES_DEFAULT_ELASTIC_CHUNK_SIZE,
        refresh=settings.TEST,
    )
    if errors or succeeded != len(actions):
        raise IndexWriteError(f"{len(actions) - succeeded} of {len(actions)} bulk items failed")


def _verified_delete_by_query(index: str, query: dict) -> None:
    response = es_client().delete_by_query(
        index=index, query=query, conflicts="abort", refresh=settings.TEST
    )
    total = response.get("total")
    deleted = response.get("deleted")
    version_conflicts = response.get("version_conflicts")
    valid_counts = all(
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
        for value in (total, deleted, version_conflicts)
    )
    if (
        response.get("timed_out") is not False
        or response.get("failures") != []
        or not valid_counts
        or version_conflicts != 0
        or deleted != total
    ):
        raise IndexWriteError(f"delete_by_query on {index} did not complete cleanly")


class RetrievalIndexUnavailable(Exception):
    """No usable physical index is bound to the requested alias."""


def configured_index_meta() -> dict:
    """The `_meta` payload the current configuration expects on an active index."""
    return build_index_meta(
        configured_embedding_recipe(),
        similarity=SIMILARITY,
        index_options=VECTOR_INDEX_OPTIONS,
        schema_version=SCHEMA_VERSION,
    )


def create_write_generation(*, timestamp: datetime, meta: dict) -> str:
    """Create a physical index, stamp its `_meta`, then move the write alias to it.

    Stamping precedes the alias move, so a live task can never reach a generation through
    the write alias before it has a validated recipe; a crash in between leaves an
    un-aliased orphan, not a reachable un-stamped index.
    """
    mapping_payload, mapping_digest = mapping_fingerprint(
        dims=VECTOR_DIMS,
        similarity=SIMILARITY,
        index_options=VECTOR_INDEX_OPTIONS,
        schema_version=SCHEMA_VERSION,
    )
    expected_mapping_meta = {**mapping_payload, "digest": mapping_digest}
    if not isinstance(meta, Mapping) or meta.get("mapping") != expected_mapping_meta:
        raise InvalidIndexMeta(
            "generation _meta mapping does not describe the ChunkDocument mapping"
        )

    name = f"{ChunkDocument.Index.base_name}_{timestamp.strftime('%Y%m%d%H%M%S')}"
    ChunkDocument.init(index=name)
    write_index_meta(name, meta)
    ChunkDocument._update_alias(ChunkDocument.Index.write_alias, name)
    return name


def resolve_active_targets() -> tuple[str, ...]:
    """The concrete indexes the read and write aliases point at — de-duplicated, with
    absent aliases removed — resolved once so a mid-operation alias move can't split a
    caller's reads and writes across generations."""
    candidates = (
        ChunkDocument.alias_points_at(ChunkDocument.Index.read_alias),
        ChunkDocument.alias_points_at(ChunkDocument.Index.write_alias),
    )
    return tuple(dict.fromkeys(target for target in candidates if target))


def recipe_for_index(index: str) -> EmbeddingRecipe:
    """The embedding recipe stamped on one concrete index.

    Reconstructed from `_meta` rather than from current settings, so a worker writing to an
    older generation embeds into the vector space that generation actually holds. An
    un-stamped or tampered `_meta` raises through ``read_index_meta``.
    """
    _require_concrete_index(index)
    meta = read_index_meta(index)
    embedding = meta["embedding"]
    return recipe_from_payload(
        {
            "provider": embedding["provider"],
            "model": embedding["model"],
            "dimensions": embedding["dimensions"],
            "document_task": embedding["document_task"],
            "query_task": meta["query"]["query_task"],
            "normalization": embedding["normalization"],
        }
    )


def resolve_read_target_and_recipe() -> tuple[str, EmbeddingRecipe]:
    """Bind a query to one concrete read index and the recipe stamped on it.

    Fails closed: a missing read alias raises rather than silently querying the write alias.
    """
    read_index = ChunkDocument.alias_points_at(ChunkDocument.Index.read_alias)
    if not read_index:
        raise RetrievalIndexUnavailable("the retrieval read alias points at no index")
    return read_index, recipe_for_index(read_index)
