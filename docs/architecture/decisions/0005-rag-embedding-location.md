# 5 - Embedding location for the RAG retrieval layer

Date: 2026-07-21

## Status

Accepted

## Context

The RAG retrieval layer turns approved knowledge-base content into scope-aware
chunks and stores each chunk as a first-class Elasticsearch document. Each chunk
needs an embedding for semantic retrieval. The open decision is narrow:
**who computes that embedding vector?**

Letting `semantic_text` re-chunk whole articles was rejected up front because it
discards the existing scope-aware chunker. The remaining viable options are:

- **A — application-side.** Python calls an embedding model via `get_embeddings()`,
  stores the vector in a `dense_vector` field (`ChunkDocument.content_vector`);
  Elasticsearch is a vector store + kNN engine.
- **B — Elasticsearch-side.** A `semantic_text` field backed by inference endpoints
  (`inference_id` for documents, `search_inference_id` for queries); Elasticsearch
  embeds on write and on query. A `custom` inference service can point at any URL
  with request/response templates and explicit input-type translation, which would
  in principle address both offline testing and Gemini task-type control
  (`ingest → RETRIEVAL_DOCUMENT`, `search → RETRIEVAL_QUERY`).

Chunking is unaffected either way; both keep our chunker's output as the retrieval
unit (under B, `chunking_settings: none` disables Elasticsearch's internal re-chunk).

Constraint: Kitsune's local development and CI both run Elasticsearch 9.2.2 on the
**Basic** license (docker-compose, `xpack.security.enabled=false`, no license
configured). **Local/CI parity is a project requirement.**

## Probe (evidence)

Run against the local Elasticsearch (9.2.2, Basic):

- License — `GET /_license` → `"type": "basic"`, status active.
- Create a custom inference endpoint —
  `PUT /_inference/text_embedding/spike-custom`
  with `{"service":"custom","service_settings":{"url":"http://127.0.0.1:9/embed", ...}}`
  → **HTTP 403**:

  ```json
  {"error":{"root_cause":[{"type":"security_exception",
   "reason":"current license is non-compliant for [inference]",
   "license.expired.feature":"inference"}],
   "type":"security_exception",
   "reason":"current license is non-compliant for [inference]",
   "license.expired.feature":"inference"},"status":403}
  ```

- Create a `semantic_text` mapping —
  `PUT /spike_semantic_test` with a `semantic_text` field → **HTTP 200** (acknowledged).

**Interpretation.** Basic permits the `semantic_text` *mapping*, but the *inference
operation* B requires is unavailable: creating our own Vertex (or deterministic fake)
inference endpoint returns a license-compliance 403. Mapping creation succeeds
regardless of license and does **not** prove inference works — Elastic documents that
indexing can still fail when inference is invoked, and the probe did not index a
document, so it did not exercise inference through any endpoint. Any user-provisioned
inference endpoint — `custom`, `googlevertexai`, or the fake endpoint we would need for
tests — is gated behind the licensed `[inference]` feature.

## Decision

Adopt **Option A (application-side embeddings)** for the RAG retrieval layer.

B requires licensed Elasticsearch for its normal runtime *and* for meaningful
integration tests (the fake-embedder endpoint itself cannot be created on Basic).
Kitsune's local and CI environments intentionally use Basic Elasticsearch, and
local/CI parity is a requirement. A permanently licensed test cluster could test B,
but would introduce infrastructure, cost, and environment coupling. Therefore A.

**Scope guardrail for A:** implement one narrow Gemini/Vertex adapter behind
`get_embeddings()` — explicit document/query task types, batching, and bounded
retries. Do **not** build a general multi-provider framework until a second provider
actually exists.

## Consequences

- Embedding vectors are computed in Python and stored in
  `ChunkDocument.content_vector`; Elasticsearch is a vector store + kNN engine.
  `semantic_text` is not used.
- Local and CI tests run fully offline on Basic Elasticsearch with a deterministic
  fake-embedder fixture; no license dependency, parity preserved.
- We own the embedding pipeline (model call, task types, batching, retries), bounded
  by the scope guardrail above.
- Our vectors are an independent embedding space from any Elastic-managed or
  Data-Engineering BigQuery vectors; not cross-queryable. Acceptable — different use
  case.
- Reversible: switching to B later reuses the chunker, index, and ingestion
  orchestration; only the embedding step and the field mapping change, plus a
  re-init and re-ingest.

## Reconsideration trigger

Revisit this decision if **dev and CI gain a durable, inference-capable Elasticsearch
license** (not a transient trial). At that point B's advantages — no application-side
embedding code, Elasticsearch-managed batching/retries, and `inference_id` version as
a natural embedding fingerprint — become available without breaking local/CI parity.
