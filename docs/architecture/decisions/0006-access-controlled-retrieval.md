# 6 - Access-controlled retrieval for private knowledge-base content

Date: 2026-07-31
Updated: 2026-11-03

## Status

Accepted on 2026-11-03.

On 2026-11-02 the restricted-content policy owner approved sending private
knowledge-base text to the embedding provider (Vertex) and storing it in the retrieval
cluster. The approval covers agent and company knowledge bases alike.

## Context

Kitsune knowledge-base articles are assigned to audiences, and each audience is a
knowledge base. A public knowledge base is readable by everyone, including signed-out
visitors. A private one is readable by the members of its groups; the company group of
an enterprise company also grants its departments. An article whose original is in any
public knowledge base is public. A private article is readable by users whose effective
groups include a group of one of its knowledge bases, and by superusers and members of
Kitsune's staff group. An article in no knowledge base is readable by those privileged
users only. Translations inherit the audiences of their original document.

The retrieval layer turns approved, rendered KB HTML into chunks, sends each chunk's
text to a managed embedding provider, and stores the text, vector, and metadata in
Elasticsearch. It indexes every content-eligible article, public or private. A caller
retrieves the public content and the private content that caller may view. The existing
lexical `WikiDocument` index remains public-only.

Access control is not merely an Elasticsearch filter:

- Elasticsearch is updated asynchronously and can contain stale access metadata.
- A document's access affects which templates and includes the wiki parser may render
  into its stored HTML.
- Changing the access of an included document can therefore affect other documents whose
  own access did not change.
- Private text is processed by the embedding provider and stored in the retrieval
  cluster, which required explicit policy approval (see Status).

Company knowledge bases hold one customer's documentation, so access control now keeps
customers apart from one another as well as keeping private content from the public. The
material is product documentation, not a general secrets store. That makes eventual
revocation an acceptable tradeoff (see "Accept delayed revocation for previously
authorized rendered content").

## Decision

### Model access independently from show-for scope

Every retrieval chunk and its `ChunkSource` carry two keyword fields, derived from the
original document's audiences. In effect:

```python
visibility = "group_restricted" if document.is_restricted else "public"
access_group_ids = (
    sorted({group.id for kb in document.original.audiences for group in kb.groups})
    if document.is_restricted
    else []
)
```

`is_restricted` is true unless the original is assigned a public knowledge base, so an
article in a public knowledge base and a private one is `public` with no group IDs.
A private article in knowledge bases without groups, or in no knowledge base, is
`group_restricted` with an empty list: no caller without the staff or superuser bypass
matches it in Elasticsearch, and the database check admits only privileged callers.

`access_group_ids` uses canonical, sorted integer group IDs. Translations read the IDs
from `document.original`. The fields are included in `index_state_hash`, so a change to
access metadata is detectable without changing `content_hash` or re-embedding unchanged
text.

The per-document manifest stores `index_state_hash`, not a duplicate copy of the group
list. `visibility` is deliberately distinct from the chunker's `scope`, which
represents show-for applicability rather than authorization.

### Ingest on content eligibility alone

Retrieval uses one predicate:

```python
def is_retrieval_indexable(document) -> bool:
    """Whether the document is ingested: approved, supported KB content, whatever its audiences."""
    # Has a current revision; is not a redirect, template, or archived;
    # and is not in an excluded administrative/content category.
```

The bulk `eligible_documents()` queryset must be proven equivalent to
`is_retrieval_indexable()`. Incremental ingestion, backfill, and reconciliation all use
the same policy boundary. Access never decides whether a document is ingested; it is
stored with each chunk and enforced when the chunk is read.

The lexical index keeps its existing, behavior-preserving public-only predicate. Its
merged-locale representation is separate from the retrieval index, which stores one
source document per locale.

### Enforce source-document access at read time

The retrieval caller's identity and group IDs are derived server-side, never accepted
as caller-supplied group IDs. The caller's group IDs are the effective groups used for
knowledge-base access: the caller's direct groups plus the company group of each
enterprise company the caller belongs to, directly or through a department.

For a caller without the staff/superuser bypass, Elasticsearch pre-filters candidates
using:

```text
visibility = public
OR
(visibility = group_restricted AND access_group_ids intersects caller_group_ids)
```

Before a hit is returned or its text is placed in a prompt, the application performs
one set-based primary-database query over the bounded KB candidate IDs and revalidates:

- current content eligibility, including the approved/current revision; and
- current authorization for the caller: the original is in a public knowledge base, or
  in one that has a group among the caller's effective groups, unless the caller is
  privileged.

The Elasticsearch query uses fixed over-fetch. After database rejection, the reader
returns the remaining results, even when that produces a short page; it does not run an
adaptive refill loop. The database check is the authorization boundary for the indexed
source document. Elasticsearch filtering protects recall and reduces unnecessary
exposure inside the application but is not authoritative.

The same rule applies during a physical-index rebuild. All ingestion mutations,
including deletion and newly ineligible content, target only the current write
generation. The old read generation may therefore retain stale candidates until the
new generation passes its gate and is promoted. Database revalidation rejects those
candidates; dual-generation eviction is not part of the authorization design.

Changing a user's group membership does not require document reindexing. Queries use
current server-side membership and the database check uses current authorization.

The initial group-aware reader does not cache retrieval results or generated answers.
Introducing such a cache requires a separate reviewed design that prevents stale
rendered content from surviving beyond index convergence. Keying solely by query text,
caller ID, or a caller-group fingerprint is insufficient.

A cache containing only a query vector is outside this restriction: it contains no
selected document content or authorization decision. Every use still runs the current
Elasticsearch access filter and authoritative database revalidation.

### Let access changes converge through ordinary ingestion

Access changes use the existing freshness mechanisms rather than a separate security
workflow:

- A change that affects only `visibility` or `access_group_ids`, such as assigning an
  article to a knowledge base, a knowledge base turning public or private, or a
  knowledge base's groups changing, takes the metadata-only path because
  `index_state_hash` changes while `content_hash` remains stable. Vectors are preserved
  and nothing is embedded again.
- When an access change alters another document's rendered body, that dependent's
  `content_hash` changes and ordinary synchronization re-embeds it.
- Content that becomes ineligible, such as an archived article or one turned into a
  redirect, is evicted whatever its audiences.

The wiki parser enforces an important render-time invariant: a public document can be
included anywhere, and a private document can be included only in a private document
that is assigned to knowledge bases, all of which also contain the included document.
Every reader of the containing document can therefore read what is rendered into it.
The existing `render_document_cascade` task rerenders dependent documents after an
access change, and each resulting `Document.save()` schedules the normal hash-gated
retrieval sync.

There is no durable access-change embargo, ordered evict/rerender/resync coordinator,
pre-mutation dependency-closure capture, or stale-workflow recovery scanner. The Redis
ingestion lease continues to serialize workers; it is not authorization state.

Reconciliation repairs missed retrieval synchronization and reports direct access
drift: indexed identities whose stored access fields disagree with the database. Indexed
identities that are no longer eligible are reported and evicted. Reconciliation does
not claim to repair wiki HTML when the render cascade itself failed.

Render-cascade and retrieval-task failures must remain visible through normal Celery
failure monitoring. This decision defines no hard convergence SLA and stores no durable
record that cleanup is owed.

### Accept delayed revocation for previously authorized rendered content

For an eventual-convergence interval after an access change:

- a direct stale hit for the changed document may still be selected by Elasticsearch,
  but current database authorization rejects it;
- a different document may still contain HTML rendered from the changed document
  before its access narrowed; and
- the audience allowed to view that stale containing document may therefore retain
  access until the wiki cascade and retrieval sync complete.

Because of the parser's render-time invariant, that audience was authorized for the
included content when it was rendered. This is delayed revocation for a previously
authorized group-level audience, not strict fragment-level enforcement of the newest
policy. Individual membership can change during the convergence interval; the system
does not track historical per-user entitlement.

The original decision named per-customer isolation as a reason to revisit this risk.
Company knowledge bases make it real, and the accepted risk still holds:

- every direct hit is re-checked in the primary database on every request, so a stale
  index entry never grants access;
- the parser includes private content in another article only when every reader of that
  article can read it; and
- the residual risk is delayed revocation of content already rendered into another
  article, and only for readers who were authorized for it when it was rendered.

The document must not describe the interval as bounded unless an operational SLA and the
mechanisms that enforce it are introduced.

### Conditions for ingesting private content

Private content is ingested because all of the following hold:

1. The restricted-content policy owner approved processing and storage. The approval
   covers the embedding provider and Elasticsearch (see Status).
2. The group-aware reader implements the server-derived ES filter, authoritative
   source-document eligibility/access revalidation, and over-fetching for rejected
   candidates.
3. The reader does not cache results or generated answers.
4. Reconciliation reports direct access drift without logging group names or IDs, and
   normal task-failure monitoring covers the wiki render cascade and retrieval sync.

Reconciliation and backfill discover private articles that are not yet indexed and
perform their first, paid embedding. Existing public vectors remain reusable.

## Consequences

- The retrieval schema represents authorization from the start without overloading
  show-for scope.
- Private article text reaches the embedding provider and is stored in Elasticsearch,
  under the same retention, region, backup and operator-access setup as public content.
- Direct source-document authorization is current and database-backed at read time.
- Access changes use the ordinary signal, hash, metadata-update, deletion, rerender,
  and reconciliation paths. There is no separate durable coordinator to operate.
- During a rebuild, stale candidates may remain in the old read generation until
  promotion; all mutations use the new write generation only, and the authoritative
  database recheck prevents stale index state from granting access.
- Access-only source changes normally preserve vectors; dependent rendered-body changes
  still require re-embedding.
- Revocation of content already rendered into another document is eventually
  consistent and has no hard completion SLA.
- The lexical search index remains public-only.

## Revisit this decision when

Any of the following invalidates the accepted-risk model:

- A customer's content needs isolation stronger than group-level read access with
  eventual revocation.
- Content whose sensitivity warrants strict current-policy control, such as personal
  data or embargoed security material, enters scope.
- Product or contractual requirements introduce a strict revocation SLA.
- Operational evidence shows render/sync failures leave stale access in place too
  often or for too long.
- Result or generated-answer caching is introduced.

At that point, reconsider a durable access-change embargo and ordered dependency
closure workflow, synchronous verified eviction, or complete rendered-content
provenance with dependency-aware read-time validation.

## Alternatives considered

- **Keep retrieval public-only.** Simpler, and it keeps private text away from the
  embedding provider, but agents and company readers would get no semantic retrieval
  over their knowledge bases.
- **Trust indexed group IDs without database revalidation.** Rejected because
  asynchronous ingestion inevitably creates stale direct-access metadata.
- **Durable embargo plus ordered dependency-closure eviction.** Stronger immediate
  revocation, but deferred because it introduces new database state, synchronous
  closure capture, recovery, task coordination, and permanent operational burden beyond
  what the accepted risk requires.
- **Dependency-aware provenance on every chunk.** Could make rendered-fragment access
  enforceable at read time, but deferred until strict fragment-level revocation is a
  real requirement.
