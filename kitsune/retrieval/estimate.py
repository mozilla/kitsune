"""Measure a full ingestion of the current corpus without calling the provider.

Chunking and token counting are local, so this reads the database, runs the chunker, and
predicts provider requests from the configured bounds. It never calls the embedding adapter.

``request_multiplier`` measures the request reduction from cross-document batching. Request
count affects rate-limit pressure and latency, but not the amount of content billed; input
characters are reported separately so provider pricing can be applied independently.
"""

from dataclasses import dataclass
from math import ceil

from kitsune.retrieval.chunking import chunk, count_tokens
from kitsune.retrieval.eligibility import eligible_documents
from kitsune.retrieval.embeddings import (
    max_input_tokens,
    provider_request_batch_lengths,
)
from kitsune.retrieval.events import emit
from kitsune.retrieval.sync import (
    CONTENT_TYPE,
    max_batch_documents,
    max_batch_embedding_inputs,
)

DEFAULT_PAGE_SIZE = 500


@dataclass(frozen=True)
class IngestionEstimate:
    """One provider-free measurement of corpus volume and request load."""

    documents: int = 0
    chunks: int = 0
    tokens: int = 0
    characters: int = 0

    mean_chunks_per_document: float = 0.0
    p50_chunks_per_document: int = 0
    p95_chunks_per_document: int = 0
    max_chunks_per_document: int = 0

    max_tokens_per_chunk: int = 0
    # Would make the adapter refuse the whole batch. The chunker's budget should keep this
    # at zero; a non-zero count is a defect to fix before spending anything.
    chunks_over_token_limit: int = 0

    provider_requests_per_document: int = 0
    provider_requests_batched: int = 0
    # Admitted-first means an unusually large document is never rejected forever; the rest of
    # its batch falls back to individual-document sync.
    documents_deferred_by_input_bound: int = 0

    @property
    def request_multiplier(self) -> float | None:
        """Per-document requests divided by batched requests, or ``None`` for no inputs."""
        if not self.provider_requests_batched:
            return None
        return self.provider_requests_per_document / self.provider_requests_batched


def _percentile(sorted_counts: list[int], fraction: float) -> int:
    if not sorted_counts:
        return 0
    # Nearest-rank on a sorted list: no interpolation, so every reported value is one a real
    # document actually has.
    rank = max(0, ceil(fraction * len(sorted_counts)) - 1)
    return sorted_counts[rank]


def _batched_requests(
    document_tokens: list[list[int]], page_size: int, max_documents: int, max_inputs: int
) -> tuple[int, int]:
    """Predict requests and input-bound deferrals for the real dispatch path.

    Backfill first passes ``page_size`` ids to ``enqueue_document_batch``, which slices them by
    ``max_documents``. Each task admits documents until ``max_inputs`` would be exceeded,
    always admitting its first document. Overflow returns to ordinary per-document sync.
    """
    requests = 0
    deferred = 0
    for page_start in range(0, len(document_tokens), page_size):
        page = document_tokens[page_start : page_start + page_size]
        for batch_start in range(0, len(page), max_documents):
            admitted: list[int] = []
            for position, tokens in enumerate(page[batch_start : batch_start + max_documents]):
                if position and len(admitted) + len(tokens) > max_inputs:
                    deferred += 1
                    requests += len(provider_request_batch_lengths(tokens))
                else:
                    admitted.extend(tokens)
            requests += len(provider_request_batch_lengths(admitted))
    return requests, deferred


def estimate_ingestion(*, locales=(), page_size: int = DEFAULT_PAGE_SIZE) -> IngestionEstimate:
    """Measure the corpus and predict the provider requests made by a full backfill."""
    if isinstance(page_size, bool) or not isinstance(page_size, int) or page_size <= 0:
        raise ValueError("page_size must be a positive integer")

    # Eligibility is enforced in SQL. Ingestion metadata is irrelevant to this estimate, so
    # avoid loading its related objects and defer every document field except the chunker inputs.
    documents = (
        eligible_documents().select_related(None).prefetch_related(None).only("html", "title")
    )
    if locales := tuple(locales):
        documents = documents.filter(locale__in=locales)

    token_limit = max_input_tokens()
    document_tokens: list[list[int]] = []
    tokens = 0
    characters = 0
    max_tokens_per_chunk = 0
    over_limit = 0
    per_document_requests = 0

    for document in documents.order_by("pk").iterator(chunk_size=page_size):
        chunks = chunk(CONTENT_TYPE, document.html, title=document.title)
        chunk_tokens = [count_tokens(item.text) for item in chunks]
        document_tokens.append(chunk_tokens)
        per_document_requests += len(provider_request_batch_lengths(chunk_tokens))
        characters += sum(len(item.text) for item in chunks)
        for item_tokens in chunk_tokens:
            tokens += item_tokens
            max_tokens_per_chunk = max(max_tokens_per_chunk, item_tokens)
            over_limit += item_tokens > token_limit

    batched_requests, deferred = _batched_requests(
        document_tokens,
        page_size,
        max_batch_documents(),
        max_batch_embedding_inputs(),
    )
    counts = [len(items) for items in document_tokens]
    sorted_counts = sorted(counts)
    estimate = IngestionEstimate(
        documents=len(counts),
        chunks=sum(counts),
        tokens=tokens,
        characters=characters,
        mean_chunks_per_document=(sum(counts) / len(counts)) if counts else 0.0,
        p50_chunks_per_document=_percentile(sorted_counts, 0.50),
        p95_chunks_per_document=_percentile(sorted_counts, 0.95),
        max_chunks_per_document=sorted_counts[-1] if sorted_counts else 0,
        max_tokens_per_chunk=max_tokens_per_chunk,
        chunks_over_token_limit=over_limit,
        provider_requests_per_document=per_document_requests,
        provider_requests_batched=batched_requests,
        documents_deferred_by_input_bound=deferred,
    )
    emit(
        "retrieval.estimate.completed",
        content_type=CONTENT_TYPE,
        documents=estimate.documents,
        chunks=estimate.chunks,
        tokens=estimate.tokens,
        characters=estimate.characters,
        max_chunks_per_document=estimate.max_chunks_per_document,
        max_tokens_per_chunk=estimate.max_tokens_per_chunk,
        chunks_over_token_limit=estimate.chunks_over_token_limit,
        provider_requests_per_document=estimate.provider_requests_per_document,
        provider_requests_batched=estimate.provider_requests_batched,
        documents_deferred_by_input_bound=estimate.documents_deferred_by_input_bound,
    )
    return estimate
