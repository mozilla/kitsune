import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import ClassVar

from django.conf import settings
from elasticsearch.dsl import field
from elasticsearch.dsl.types import DenseVectorIndexOptions
from elasticsearch.helpers import bulk

from kitsune.retrieval.chunking import CHUNKING_GENERATION, Chunk
from kitsune.retrieval.fingerprints import content_hash, index_state_hash, scope_envelope
from kitsune.search.base import SumoDocument
from kitsune.search.es_utils import es_client
from kitsune.search.fields import SumoLocaleAwareKeywordField, SumoLocaleAwareTextField

# Single source of truth for the vector dimensionality, shared with the embedding recipe
# (settings.RETRIEVAL_EMBEDDING_DIMENSIONS) so the mapping and the vectors can't disagree.
VECTOR_DIMS = settings.RETRIEVAL_EMBEDDING_DIMENSIONS

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


def _canonical_group_ids(values) -> tuple[int, ...]:
    if isinstance(values, str | bytes):
        raise InvalidDocumentState("access_group_ids must be a sequence of integers")
    try:
        items = tuple(values)
    except TypeError as exc:
        raise InvalidDocumentState("access_group_ids must be a sequence of integers") from exc
    for value in items:
        _require_int(value, "access_group_ids item", minimum=1)
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
        similarity="cosine",
        index=True,
        index_options=DenseVectorIndexOptions(type="hnsw", m=16, ef_construction=100),
    )
    scope = field.Object(enabled=False)  # lossless, opaque; _source only (§4.3)
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

    Structurally satisfies ``fingerprints.ChunkStateSource``. Hashes are worker-computed
    (§7), never caller-supplied, so this carries no ``content_hash``.
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


def index_chunks(chunks: list[Chunk], source: ChunkSource) -> None:
    locale = source.locale
    identity = source.identity
    positions = [chunk.position for chunk in chunks]
    for position in positions:
        _require_int(position, "chunk position", minimum=0)
    if positions != list(range(len(chunks))):
        raise InvalidDocumentState("chunk positions must be contiguous and start at zero")

    # Worker-computed per-document state (§7); repeated on every chunk for recovery.
    document_hash = content_hash(chunks)
    state_hash = index_state_hash(chunks, source)
    indexed_on = datetime.now(tz=UTC)
    actions = []
    for chunk in chunks:
        doc = ChunkDocument(
            kind=CHUNK_KIND,
            content_text={locale: chunk.text},
            content_type=source.content_type,
            object_id=source.object_id,
            family_id=source.family_id,
            locale=locale,
            applies_to=sorted(chunk.applies_to),
            scope=scope_envelope(chunk.scope),
            scope_clause_count=len(chunk.scope),
            heading_path=chunk.heading_path,
            position=chunk.position,
            visibility=source.visibility,
            access_group_ids=list(source.access_group_ids),
            content_hash=document_hash,
            index_state_hash=state_hash,
            chunking_generation=CHUNKING_GENERATION,
            indexed_on=indexed_on,
            title={locale: source.title},
            summary={locale: source.summary},
            keywords={locale: source.keywords},
            slug={locale: source.slug},
            category=source.category,
            product_ids=list(source.product_ids),
            topic_ids=list(source.topic_ids),
            updated=source.updated,
        )
        doc.meta.id = chunk_id(identity, chunk.position)
        actions.append(doc.to_action(action="index", is_bulk=True))

    bulk(
        es_client(),
        actions,
        chunk_size=settings.ES_DEFAULT_ELASTIC_CHUNK_SIZE,
        refresh=settings.TEST,
    )


def delete_chunks_for(*, content_type: str, object_id: str, locale: str) -> None:
    es_client().delete_by_query(
        index=ChunkDocument.Index.write_alias,
        query={
            "bool": {
                "filter": [
                    {"term": {"content_type": content_type}},
                    {"term": {"object_id": object_id}},
                    {"term": {"locale": locale}},
                ]
            }
        },
        refresh=settings.TEST,
    )
