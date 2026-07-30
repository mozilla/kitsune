"""Canonical serialization, per-document hashes, and index-level fingerprints.

Pure functions on explicit inputs so this module carries no dependency on the sync core
or the ES mapping value objects. Two per-document hashes drive the worker's cheapest
correct outcome; three index-level fingerprints classify whether an index change needs
a re-embed, a vector copy, or only a `_meta` update.
"""

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from enum import Enum
from typing import Protocol

from kitsune.retrieval.chunking import Chunk
from kitsune.retrieval.embeddings import (
    EmbeddingRecipe,
    InvalidEmbeddingRecipe,
    recipe_from_payload,
)
from kitsune.search.es_utils import es_client

SCOPE_ENVELOPE_VERSION = 1
_SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")
_META_FIELDS = {
    "embedding": {
        "provider": str,
        "model": str,
        "dimensions": int,
        "document_task": str,
        "normalization": str,
    },
    "query": {
        "provider": str,
        "model": str,
        "dimensions": int,
        "query_task": str,
        "normalization": str,
    },
    "mapping": {
        "dimensions": int,
        "similarity": str,
        "index_options": dict,
        "schema_version": int,
    },
}
_INDEX_OPTION_FIELDS = {"type": str, "m": int, "ef_construction": int}


class ChunkStateSource(Protocol):
    """The shared per-document metadata `index_state_hash` reads off a source.

    ``ChunkSource`` satisfies this structural contract. Keeping it as a Protocol avoids
    making the pure fingerprint module depend on the concrete Elasticsearch model.
    """

    @property
    def title(self) -> str: ...

    @property
    def summary(self) -> str: ...

    @property
    def keywords(self) -> str: ...

    @property
    def slug(self) -> str: ...

    @property
    def category(self) -> str: ...

    @property
    def family_id(self) -> str: ...

    @property
    def product_ids(self) -> Sequence[str]: ...

    @property
    def topic_ids(self) -> Sequence[str]: ...

    @property
    def visibility(self) -> str: ...

    @property
    def access_group_ids(self) -> Sequence[int]: ...

    @property
    def updated(self) -> datetime: ...


def canonical_json(value: object) -> bytes:
    """Deterministic JSON: object keys sorted, list/tuple order preserved, fixed separators."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def _digest(payload: object) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def scope_envelope(scope: Sequence[frozenset[str]]) -> dict:
    """Encode scope canonically while preserving clause order and sorting selectors.

    The state hash and stored ``_source`` share this function so their scope
    representations cannot drift.
    """
    return {"version": SCOPE_ENVELOPE_VERSION, "clauses": [sorted(clause) for clause in scope]}


def _normalize_timestamp(value: datetime) -> str:
    """Normalize an aware timestamp to UTC with fixed microsecond precision."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("updated must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def content_hash(chunks: Sequence[Chunk]) -> str:
    """Hash exactly the embedding inputs: the ordered chunk texts."""
    return _digest([chunk.text for chunk in chunks])


def index_state_hash(chunks: Sequence[Chunk], source: ChunkStateSource) -> str:
    """Hash metadata whose drift requires reindexing without recomputing vectors."""
    payload = {
        "chunks": [
            {"heading_path": chunk.heading_path, "scope": scope_envelope(chunk.scope)}
            for chunk in chunks
        ],
        "source": {
            "title": source.title,
            "summary": source.summary,
            "keywords": source.keywords,
            "slug": source.slug,
            "category": source.category,
            "family_id": source.family_id,
            "product_ids": sorted(source.product_ids),
            "topic_ids": sorted(source.topic_ids),
            "visibility": source.visibility,
            "access_group_ids": sorted(source.access_group_ids),
            "updated": _normalize_timestamp(source.updated),
        },
    }
    return _digest(payload)


def document_embedding_fingerprint(recipe: EmbeddingRecipe) -> tuple[dict, str]:
    """Identity of the stored vectors' embedding space. Excludes the query task so a
    query-only recipe change does not force a re-embed."""
    payload = {
        "provider": recipe.provider,
        "model": recipe.model,
        "dimensions": recipe.dimensions,
        "document_task": recipe.document_task,
        "normalization": recipe.normalization,
    }
    return payload, _digest(payload)


def query_embedding_fingerprint(recipe: EmbeddingRecipe) -> tuple[dict, str]:
    """Identity of the query-encoding profile bound to the index (not an input to any
    stored vector)."""
    payload = {
        "provider": recipe.provider,
        "model": recipe.model,
        "dimensions": recipe.dimensions,
        "query_task": recipe.query_task,
        "normalization": recipe.normalization,
    }
    return payload, _digest(payload)


def mapping_fingerprint(
    *, dims: int, similarity: str, index_options: dict, schema_version: int
) -> tuple[dict, str]:
    """Identity of vector-mapping properties that require a new physical index.

    Analyzers and synonyms are deliberately excluded: changing lexical analysis must not
    re-embed the corpus.
    """
    payload = {
        "dimensions": dims,
        "similarity": similarity,
        "index_options": dict(index_options),
        "schema_version": schema_version,
    }
    return payload, _digest(payload)


def build_index_meta(
    recipe: EmbeddingRecipe, *, similarity: str, index_options: dict, schema_version: int
) -> dict:
    """Build readable per-index `_meta` with a digest for each compatibility boundary."""
    doc_payload, doc_digest = document_embedding_fingerprint(recipe)
    query_payload, query_digest = query_embedding_fingerprint(recipe)
    mapping_payload, mapping_digest = mapping_fingerprint(
        dims=recipe.dimensions,
        similarity=similarity,
        index_options=index_options,
        schema_version=schema_version,
    )
    return {
        "embedding": {**doc_payload, "digest": doc_digest},
        "query": {**query_payload, "digest": query_digest},
        "mapping": {**mapping_payload, "digest": mapping_digest},
    }


class IndexMetaAction(Enum):
    NONE = "none"
    QUERY_META_UPDATE = "query_meta_update"
    COPY_VECTORS = "copy_vectors"
    REEMBED = "reembed"


def classify_meta_mismatch(current: dict, desired: dict) -> IndexMetaAction:
    """Choose the cheapest safe response to an index `_meta` difference.

    An embedding-space change wins (re-embed), followed by a vector-mapping change
    (copy vectors), then a query-recipe change (`_meta` update only).
    """
    if current["embedding"]["digest"] != desired["embedding"]["digest"]:
        return IndexMetaAction.REEMBED
    if current["mapping"]["digest"] != desired["mapping"]["digest"]:
        return IndexMetaAction.COPY_VECTORS
    if current["query"]["digest"] != desired["query"]["digest"]:
        return IndexMetaAction.QUERY_META_UPDATE
    return IndexMetaAction.NONE


class InvalidIndexMeta(ValueError):
    """A concrete index's stored `_meta` is absent, malformed, or fails digest validation."""


def write_index_meta(index: str, meta: dict) -> None:
    """Stamp the `_meta` of a concrete physical index via the low-level mapping API."""
    _validate_index_meta(meta)
    es_client().indices.put_mapping(index=index, meta=meta)


def read_index_meta(index: str) -> dict:
    """Read and re-validate a concrete index's `_meta`, failing closed on any tampering."""
    response = es_client().indices.get_mapping(index=index)
    raw = getattr(response, "body", response)
    if not isinstance(raw, Mapping):
        raise InvalidIndexMeta(f"index {index!r} returned a malformed mapping response")
    if len(raw) != 1:
        raise InvalidIndexMeta(f"expected exactly one index for {index!r}, got {len(raw)}")
    index_mapping = next(iter(raw.values()))
    if not isinstance(index_mapping, Mapping):
        raise InvalidIndexMeta(f"index {index!r} returned a malformed mapping")
    mappings = index_mapping.get("mappings")
    if not isinstance(mappings, Mapping):
        raise InvalidIndexMeta(f"index {index!r} returned no valid mappings object")
    meta = mappings.get("_meta")
    if not meta:
        raise InvalidIndexMeta(f"index {index!r} has no _meta")
    _validate_index_meta(meta)
    return meta


def _validate_index_meta(meta: dict) -> None:
    """Validate `_meta` structure, recipe compatibility, and every section digest."""
    if not isinstance(meta, dict) or set(meta) != set(_META_FIELDS):
        raise InvalidIndexMeta("_meta must contain exactly embedding, query, and mapping")

    for section, field_types in _META_FIELDS.items():
        block = meta[section]
        if not isinstance(block, dict):
            raise InvalidIndexMeta(f"_meta section {section!r} must be an object")

        expected_fields = {*field_types, "digest"}
        if set(block) != expected_fields:
            raise InvalidIndexMeta(
                f"_meta section {section!r} must contain exactly {sorted(expected_fields)!r}"
            )

        for name, expected_type in field_types.items():
            value = block[name]
            if expected_type is int:
                valid_type = isinstance(value, int) and not isinstance(value, bool)
            else:
                valid_type = isinstance(value, expected_type)
            if not valid_type:
                raise InvalidIndexMeta(
                    f"_meta field {section}.{name} must be {expected_type.__name__}"
                )

        digest = block["digest"]
        if not isinstance(digest, str) or not _SHA256_HEX.fullmatch(digest):
            raise InvalidIndexMeta(f"_meta section {section!r} has an invalid digest")

        payload = {key: value for key, value in block.items() if key != "digest"}
        if _digest(payload) != digest:
            raise InvalidIndexMeta(f"_meta section {section!r} failed digest validation")

    embedding = meta["embedding"]
    query = meta["query"]
    mapping = meta["mapping"]

    for name in ("provider", "model", "dimensions", "normalization"):
        if embedding[name] != query[name]:
            raise InvalidIndexMeta(f"embedding and query {name} values must match")
    if mapping["dimensions"] != embedding["dimensions"]:
        raise InvalidIndexMeta("mapping dimensions must match embedding dimensions")

    for section, name in (
        ("embedding", "dimensions"),
        ("mapping", "dimensions"),
        ("mapping", "schema_version"),
    ):
        if meta[section][name] <= 0:
            raise InvalidIndexMeta(f"_meta field {section}.{name} must be positive")

    index_options = mapping["index_options"]
    if set(index_options) != set(_INDEX_OPTION_FIELDS):
        raise InvalidIndexMeta(
            f"_meta mapping.index_options must contain exactly {sorted(_INDEX_OPTION_FIELDS)!r}"
        )
    for name, expected_type in _INDEX_OPTION_FIELDS.items():
        value = index_options[name]
        if expected_type is int:
            valid_type = isinstance(value, int) and not isinstance(value, bool) and value > 0
        else:
            valid_type = isinstance(value, expected_type) and bool(value)
        if not valid_type:
            raise InvalidIndexMeta(
                f"_meta field mapping.index_options.{name} must be a valid "
                f"{expected_type.__name__}"
            )
    if not mapping["similarity"]:
        raise InvalidIndexMeta("_meta field mapping.similarity must not be empty")

    try:
        recipe_from_payload(
            {
                "provider": embedding["provider"],
                "model": embedding["model"],
                "dimensions": embedding["dimensions"],
                "document_task": embedding["document_task"],
                "query_task": query["query_task"],
                "normalization": embedding["normalization"],
            }
        )
    except InvalidEmbeddingRecipe as exc:
        raise InvalidIndexMeta(f"_meta contains an invalid embedding recipe: {exc}") from exc
