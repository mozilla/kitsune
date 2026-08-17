"""Exact-query vector caching shared by interactive retrieval consumers."""

import hashlib
from typing import Literal

from django.conf import settings
from django.core.cache import cache

from kitsune.retrieval.embeddings import (
    EmbeddingRecipe,
    InvalidEmbeddingResponse,
    get_embeddings,
    recipe_to_payload,
    validate_embeddings,
)
from kitsune.retrieval.fingerprints import query_embedding_fingerprint

_CACHE_NAMESPACE = "retrieval:query-vector:v1"
CacheLookupOutcome = Literal["hit", "miss", "invalid", "read_failed"]
CacheWriteOutcome = Literal["stored", "write_failed"]


def get_cached_query_vector(
    query: str, recipe: EmbeddingRecipe
) -> tuple[list[float] | None, CacheLookupOutcome]:
    """Return a validated exact-query cache hit and its bounded lookup outcome."""
    key = _query_vector_cache_key(query, recipe)
    try:
        vector = cache.get(key)
    except Exception:
        return None, "read_failed"

    if vector is None:
        return None, "miss"
    try:
        if not isinstance(vector, list):
            raise InvalidEmbeddingResponse("cached embedding is not a list")
        validate_embeddings([vector], [query], recipe)
    except InvalidEmbeddingResponse:
        try:
            cache.delete(key)
        except Exception:
            pass
        return None, "invalid"
    return [float(value) for value in vector], "hit"


def embed_and_cache_query_vector(
    query: str, recipe: EmbeddingRecipe
) -> tuple[list[float], CacheWriteOutcome]:
    """Embed one authorized cache miss and report whether the cache write succeeded."""
    [vector] = get_embeddings([query], task="query", recipe=recipe)
    try:
        cache.set(
            _query_vector_cache_key(query, recipe),
            vector,
            timeout=settings.RETRIEVAL_QUERY_VECTOR_CACHE_TTL_SECONDS,
        )
    except Exception:
        return vector, "write_failed"
    return vector, "stored"


def _query_vector_cache_key(query: str, recipe: EmbeddingRecipe) -> str:
    recipe_to_payload(recipe)  # Fail closed on invalid recipes, including on cache hits.
    recipe_digest = query_embedding_fingerprint(recipe)[1]
    query_digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
    return f"{_CACHE_NAMESPACE}:{recipe_digest}:{query_digest}"
