import hashlib
import logging
import math
import random
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from functools import cache
from numbers import Real
from typing import Literal, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from kitsune.retrieval.chunking import count_tokens
from kitsune.retrieval.events import emit

FAKE_BACKEND = "fake"
VERTEX_BACKEND = "vertex"

DEFAULT_DOCUMENT_TASK = "RETRIEVAL_DOCUMENT"
DEFAULT_QUERY_TASK = "RETRIEVAL_QUERY"
DEFAULT_NORMALIZATION = "none"
MIN_EMBEDDING_TIMEOUT_SECONDS = 0.001

_MAX_ATTEMPTS = 4
_BACKOFF_BASE = 0.5
_NORMALIZATIONS = frozenset({"none", "l2"})
# Vertex allows 250 inputs and 2,048 tokens per input for the currently supported
# Google embedding models. The provider remains authoritative because this estimate
# deliberately avoids a separate remote token-count request.
_VERTEX_MAX_BATCH_SIZE = 250
_VERTEX_MAX_INPUT_TOKENS = 2_048
_RECIPE_FIELDS = frozenset(
    {
        "provider",
        "model",
        "dimensions",
        "document_task",
        "query_task",
        "normalization",
    }
)


class InvalidEmbeddingRecipe(ValueError):
    """The embedding recipe cannot produce compatible document/query vectors."""


class InvalidEmbeddingResponse(ValueError):
    """The provider returned vectors that are unsafe to index."""


@dataclass(frozen=True)
class EmbeddingRecipe:
    provider: str
    model: str
    dimensions: int
    document_task: str
    query_task: str
    normalization: str


@dataclass
class _ProviderStats:
    request_count: int = 0


def configured_embedding_recipe() -> EmbeddingRecipe:
    recipe = EmbeddingRecipe(
        provider=settings.RETRIEVAL_EMBEDDING_BACKEND,
        model=settings.RETRIEVAL_EMBEDDING_MODEL,
        dimensions=settings.RETRIEVAL_EMBEDDING_DIMENSIONS,
        document_task=DEFAULT_DOCUMENT_TASK,
        query_task=DEFAULT_QUERY_TASK,
        normalization=DEFAULT_NORMALIZATION,
    )
    try:
        _validate_recipe(recipe)
    except InvalidEmbeddingRecipe as exc:
        raise ImproperlyConfigured(str(exc)) from exc
    _configured_batch_size()
    return recipe


def _validate_recipe(recipe: EmbeddingRecipe) -> None:
    string_fields = {
        "provider": recipe.provider,
        "model": recipe.model,
        "document_task": recipe.document_task,
        "query_task": recipe.query_task,
        "normalization": recipe.normalization,
    }
    for name, value in string_fields.items():
        if not isinstance(value, str):
            raise InvalidEmbeddingRecipe(f"{name} must be a string")

    if recipe.provider not in _EMBED_BACKENDS:
        raise InvalidEmbeddingRecipe(f"unknown embedding backend {recipe.provider!r}")
    if (
        not isinstance(recipe.dimensions, int)
        or isinstance(recipe.dimensions, bool)
        or recipe.dimensions <= 0
    ):
        raise InvalidEmbeddingRecipe("embedding dimensions must be a positive integer")
    if not recipe.document_task:
        raise InvalidEmbeddingRecipe("document_task must not be empty")
    if not recipe.query_task:
        raise InvalidEmbeddingRecipe("query_task must not be empty")
    if recipe.normalization not in _NORMALIZATIONS:
        raise InvalidEmbeddingRecipe(f"unknown embedding normalization {recipe.normalization!r}")
    if recipe.provider == VERTEX_BACKEND and not recipe.model:
        raise InvalidEmbeddingRecipe("a model is required for the vertex backend")


def recipe_to_payload(recipe: EmbeddingRecipe) -> dict[str, str | int]:
    _validate_recipe(recipe)
    return asdict(recipe)


def recipe_from_payload(payload: Mapping[str, object]) -> EmbeddingRecipe:
    if set(payload) != _RECIPE_FIELDS:
        raise InvalidEmbeddingRecipe("embedding recipe payload has unexpected fields")

    recipe = EmbeddingRecipe(
        provider=cast(str, payload["provider"]),
        model=cast(str, payload["model"]),
        dimensions=cast(int, payload["dimensions"]),
        document_task=cast(str, payload["document_task"]),
        query_task=cast(str, payload["query_task"]),
        normalization=cast(str, payload["normalization"]),
    )
    _validate_recipe(recipe)
    return recipe


def get_embeddings(
    texts: Sequence[str],
    *,
    task: Literal["document", "query"],
    recipe: EmbeddingRecipe,
) -> list[list[float]]:
    """Return validated embeddings in the same order as the input texts."""
    _validate_recipe(recipe)
    if task == "document":
        task_type = recipe.document_task
    elif task == "query":
        task_type = recipe.query_task
    else:
        raise ValueError(f"unknown embedding task {task!r}")

    if isinstance(texts, str | bytes):
        raise TypeError("embedding inputs must be a sequence of strings")
    inputs = list(texts)
    if not inputs:
        return []
    if not all(isinstance(text, str) for text in inputs):
        raise TypeError("embedding inputs must be strings")

    started = time.monotonic()
    character_count = sum(len(text) for text in inputs)
    stats = _ProviderStats()
    try:
        vectors = _EMBED_BACKENDS[recipe.provider](
            inputs,
            task_type=task_type,
            recipe=recipe,
            stats=stats,
        )
        validate_embeddings(vectors, inputs, recipe)
    except Exception as exc:
        # Only the exception's type: a provider message can quote the input or the credential.
        emit(
            "retrieval.embeddings.failed",
            level=logging.ERROR,
            provider=recipe.provider,
            model=recipe.model,
            task=task,
            text_count=len(inputs),
            character_count=character_count,
            request_count=stats.request_count,
            error_type=type(exc).__name__,
            duration_ms=_elapsed_ms(started),
        )
        raise
    emit(
        "retrieval.embeddings.completed",
        provider=recipe.provider,
        model=recipe.model,
        task=task,
        dimensions=recipe.dimensions,
        text_count=len(inputs),
        # A bounded measure of input size without recording the input itself.
        character_count=character_count,
        request_count=stats.request_count,
        duration_ms=_elapsed_ms(started),
    )
    return vectors


def _elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def validate_embeddings(
    vectors: Sequence[Sequence[object]], texts: Sequence[str], recipe: EmbeddingRecipe
) -> None:
    if len(vectors) != len(texts):
        raise InvalidEmbeddingResponse(f"expected {len(texts)} vectors, got {len(vectors)}")
    for vector in vectors:
        if len(vector) != recipe.dimensions:
            raise InvalidEmbeddingResponse(
                f"expected dimension {recipe.dimensions}, got {len(vector)}"
            )
        numeric_vector: list[float] = []
        for value in vector:
            if not isinstance(value, Real) or isinstance(value, bool) or not math.isfinite(value):
                raise InvalidEmbeddingResponse(
                    "embedding contains a non-numeric or non-finite value"
                )
            numeric_vector.append(float(value))
        if recipe.normalization == "l2":
            norm = math.sqrt(sum(value * value for value in numeric_vector))
            if abs(norm - 1.0) > 1e-3:
                raise InvalidEmbeddingResponse("embedding is not unit-norm under l2 normalization")


def _fake_embed(
    texts: list[str], *, task_type: str, recipe: EmbeddingRecipe, stats: _ProviderStats
) -> list[list[float]]:
    byte_count = recipe.dimensions * 4  # 4 bytes per float
    vectors = []
    for text in texts:
        seed = f"{recipe.model}\x00{task_type}\x00{text}".encode()
        raw = b""
        counter = 0
        while len(raw) < byte_count:
            raw += hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
            counter += 1
        # Map each 4-byte word to a float in [-1, 1).
        vectors.append(
            [int.from_bytes(raw[i : i + 4], "big") / 2**31 - 1.0 for i in range(0, byte_count, 4)]
        )
        if recipe.normalization == "l2":
            norm = math.sqrt(sum(value * value for value in vectors[-1]))
            if norm == 0:
                vectors[-1][0] = 1.0
            else:
                vectors[-1] = [value / norm for value in vectors[-1]]
    return vectors


def _vertex_embed(
    texts: list[str], *, task_type: str, recipe: EmbeddingRecipe, stats: _ProviderStats
) -> list[list[float]]:
    if any(count_tokens(text) > _VERTEX_MAX_INPUT_TOKENS for text in texts):
        raise InvalidEmbeddingResponse(
            "embedding input exceeds Vertex's estimated per-input token limit"
        )

    batch_size = min(_configured_batch_size(), _VERTEX_MAX_BATCH_SIZE)
    timeout_ms = _configured_timeout_ms()
    client = _vertex_client(recipe.model)
    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        batch_vectors = _embed_batch_with_retry(
            client,
            batch,
            task_type=task_type,
            dimensions=recipe.dimensions,
            timeout_ms=timeout_ms,
            stats=stats,
        )
        validate_embeddings(batch_vectors, batch, recipe)
        vectors.extend(batch_vectors)
    return vectors


def _configured_timeout_ms() -> int:
    """Return the configured request deadline in provider milliseconds."""
    timeout = settings.RETRIEVAL_EMBEDDING_TIMEOUT_SECONDS
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, int | float)
        or not math.isfinite(timeout)
        or timeout < MIN_EMBEDDING_TIMEOUT_SECONDS
    ):
        raise ImproperlyConfigured(
            "RETRIEVAL_EMBEDDING_TIMEOUT_SECONDS must be a finite number of seconds "
            "of at least one millisecond"
        )
    return int(timeout * 1000)


def _configured_batch_size() -> int:
    batch_size = settings.RETRIEVAL_EMBEDDING_BATCH_SIZE
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or batch_size <= 0:
        raise ImproperlyConfigured("RETRIEVAL_EMBEDDING_BATCH_SIZE must be a positive integer")
    return batch_size


def _embed_batch_with_retry(
    client,
    batch: list[str],
    *,
    task_type: str,
    dimensions: int,
    timeout_ms: int,
    stats: _ProviderStats,
) -> list[list[float]]:
    from google.api_core import exceptions as gexc
    from google.genai import errors as genai_errors
    from httpx import TimeoutException as HttpxTimeout
    from requests import Timeout as RequestsTimeout

    provider_errors = (
        genai_errors.APIError,
        gexc.ResourceExhausted,
        gexc.ServiceUnavailable,
        gexc.TooManyRequests,
        gexc.InternalServerError,
        gexc.DeadlineExceeded,
        gexc.GatewayTimeout,
        gexc.BadGateway,
        HttpxTimeout,
        RequestsTimeout,
    )
    for attempt in range(_MAX_ATTEMPTS):
        try:
            stats.request_count += 1
            return _request_vertex_embeddings(
                client, batch, task_type=task_type, dimensions=dimensions, timeout_ms=timeout_ms
            )
        except provider_errors as exc:
            if isinstance(exc, genai_errors.APIError) and not (
                exc.code == 429 or 500 <= exc.code < 600
            ):
                raise
            if attempt == _MAX_ATTEMPTS - 1:
                raise
            emit(
                "retrieval.embeddings.retried",
                level=logging.WARNING,
                attempt=attempt + 1,
                max_attempts=_MAX_ATTEMPTS,
                batch_size=len(batch),
                error_type=type(exc).__name__,
            )
            time.sleep(_BACKOFF_BASE * 2**attempt + random.uniform(0, _BACKOFF_BASE))
    raise AssertionError("retry loop exited unexpectedly")


def _request_vertex_embeddings(
    client, batch: list[str], *, task_type: str, dimensions: int, timeout_ms: int
) -> list[list[float]]:
    """Call Google Gen AI directly so truncation cannot be hidden by the LangChain wrapper."""
    from google.genai.types import EmbedContentConfig, HttpOptions

    response = client.client.models.embed_content(
        model=client.model_name,
        contents=batch,
        config=EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=dimensions,
            auto_truncate=False,
            http_options=HttpOptions(timeout=timeout_ms),
        ),
    )
    embeddings = response.embeddings or []
    vectors: list[list[float]] = []
    for embedding in embeddings:
        statistics = embedding.statistics
        if statistics is None or statistics.truncated is not False:
            raise InvalidEmbeddingResponse(
                "Vertex embedding response has invalid or truncated token statistics"
            )
        if embedding.values is None:
            raise InvalidEmbeddingResponse("Vertex embedding response has no vector values")
        vectors.append(list(embedding.values))
    return vectors


@cache
def _vertex_client(model: str):
    # Imported lazily so module load and non-Vertex paths need no client or credentials.
    from langchain_google_vertexai import VertexAIEmbeddings

    # This adapter owns the retry policy; disable the client's nested retry loop.
    return VertexAIEmbeddings(model=model, max_retries=0)


_EMBED_BACKENDS = {FAKE_BACKEND: _fake_embed, VERTEX_BACKEND: _vertex_embed}
