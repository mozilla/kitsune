# 6 - Access-controlled retrieval for group-restricted KB content

Date: 2026-07-31

## Status

Proposed — pending restricted-content policy approval.

Until this decision is accepted, retrieval ingestion remains public-only: restricted
content must not be sent to the embedding provider or stored in the retrieval index.
The access fields and public-only policy boundary described below may be modeled while
inert, but there is no runtime switch that can enable restricted ingestion.

## Context

Kitsune knowledge-base documents can be restricted to one or more Django
authentication groups. A document passes the group-access check when it is
unrestricted, the caller belongs to any allowed group, or the caller is a superuser or
a member of Kitsune's staff group. Translations inherit the restrictions of their
original document.

The retrieval layer turns approved, rendered KB HTML into chunks, sends each chunk's
text to a managed embedding provider, and stores the text, vector, and metadata in
Elasticsearch. It initially indexes public content only. The desired future behavior
is for an authenticated caller to retrieve both public content and restricted content
that caller may view. The existing lexical `WikiDocument` index remains public-only.

Access control is not merely an Elasticsearch filter:

- Elasticsearch is updated asynchronously and can contain stale access metadata.
- A document's restrictions affect which templates and includes the wiki parser may
  render into its stored HTML.
- Changing the restrictions of an included document can therefore affect other
  documents whose own access rules did not change.
- Restricted text would be processed by the embedding provider and stored in the
  retrieval cluster, which requires explicit policy approval.

There is no current tenant-isolation requirement. Per-customer documentation scoping
is hypothetical, and the anticipated material is hosted product documentation rather
than a general secrets store. These constraints make eventual revocation an acceptable
tradeoff for the present system; they do not themselves authorize external processing
or indexed storage.

## Decision

### Model access independently from show-for scope

Every retrieval chunk and its `ChunkSource` carry two keyword fields:

```python
access_group_ids = sorted(
    document.original.restrict_to_groups.values_list("id", flat=True)
)
visibility = "group_restricted" if access_group_ids else "public"
```

`access_group_ids` uses canonical, sorted integer group IDs. Translations read the IDs
from `document.original`. The fields are included in `index_state_hash`, so a change to
access metadata is detectable without changing `content_hash` or re-embedding unchanged
text.

The per-document manifest stores `index_state_hash`, not a duplicate copy of the group
list. `visibility` is deliberately distinct from the chunker's `scope`, which
represents show-for applicability rather than authorization.

While ingestion is public-only, every indexed chunk has
`visibility == "public"` and `access_group_ids == []`.

### Separate content eligibility from the rollout policy

Retrieval uses three explicit predicates:

```python
def is_retrieval_content_eligible(document) -> bool:
    """Whether this is approved, supported KB content, independent of access."""
    # Has a current revision; is not a redirect, template, or archived;
    # and is not in an excluded administrative/content category.


def is_publicly_accessible(document) -> bool:
    return not document.is_restricted


def is_retrieval_indexable(document) -> bool:
    """The current public-only ingestion policy."""
    return (
        is_retrieval_content_eligible(document)
        and is_publicly_accessible(document)
    )
```

The bulk `eligible_documents()` queryset must be proven equivalent to the complete
`is_retrieval_indexable()` predicate. Incremental ingestion, backfill, and
reconciliation all use the same policy boundary.

There is no `include_restricted` argument or configuration flag. Enabling restricted
ingestion later is a deliberate code change to the object predicate, queryset,
reconciliation expectations, and tests. It cannot happen through an environment
toggle.

The lexical index keeps its existing, behavior-preserving public-only predicate. Its
merged-locale representation is separate from the retrieval index, which stores one
source document per locale.

### Enforce source-document access at read time

The retrieval caller's identity and group IDs are derived server-side, never accepted
as caller-supplied group IDs.

For a caller without the staff/superuser bypass, Elasticsearch pre-filters candidates
using:

```text
visibility = public
OR
(visibility = group_restricted AND access_group_ids intersects caller_group_ids)
```

Before a hit is returned or its text is placed in a prompt, the application
batch-loads the source documents and revalidates:

- current content eligibility, including the approved/current revision; and
- current authorization for the caller.

It fetches additional candidates as necessary to replace rejected stale hits. The
database check is the authorization boundary for the indexed source document;
Elasticsearch filtering protects recall and reduces unnecessary exposure inside the
application but is not authoritative.

Changing a user's group membership does not require document reindexing. Queries use
current server-side membership and the database check uses current authorization.

The initial group-aware reader does not cache retrieval results or generated answers.
Introducing such a cache requires a separate reviewed design that prevents stale
rendered content from surviving beyond index convergence. Keying solely by query text,
caller ID, or a caller-group fingerprint is insufficient.

### Let access changes converge through ordinary ingestion

Access changes use the existing freshness mechanisms rather than a separate security
workflow:

- While ingestion remains public-only, making a document restricted makes it
  ineligible, so ordinary synchronization evicts it. Making it public makes it newly
  eligible and indexes it.
- Once restricted ingestion is deliberately enabled, a change that affects only
  `visibility` or `access_group_ids` takes the metadata-only path because
  `index_state_hash` changes while `content_hash` remains stable.
- When an access change alters another document's rendered body, that dependent's
  `content_hash` changes and ordinary synchronization re-embeds it.

The wiki parser already enforces an important render-time invariant: it includes a
restricted document only when every group allowed to view the containing document is
also allowed to view the included document. The existing
`render_document_cascade` task rerenders dependent documents after a restriction
change, and each resulting `Document.save()` schedules the normal hash-gated retrieval
sync.

There is no durable access-change embargo, ordered evict/rerender/resync coordinator,
pre-mutation dependency-closure capture, or stale-workflow recovery scanner. The Redis
ingestion lease continues to serialize workers; it is not authorization state.

Reconciliation repairs missed retrieval synchronization and reports direct access
drift: indexed identities whose stored access fields disagree with the database or
which are indexed despite being ineligible under the active rollout policy. It does
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

This risk is accepted for the current non-tenant product-documentation use case. The
document must not describe the interval as bounded unless an operational SLA and the
mechanisms that enforce it are introduced.

### Gate restricted ingestion on policy and the secure reader

Restricted ingestion may be enabled only after all of the following hold:

1. The restricted-content policy owner approves processing and storage. Approval must
   cover the embedding provider and Elasticsearch, including retention,
   regional/data-handling requirements, backups, and operator access.
2. The group-aware reader implements the server-derived ES filter, authoritative
   source-document eligibility/access revalidation, and over-fetching for rejected
   candidates.
3. The reader does not cache results or generated answers unless a separately reviewed
   invalidation design has been implemented.
4. Reconciliation reports direct access drift without logging group names or IDs, and
   normal task-failure monitoring covers the wiki render cascade and retrieval sync.

Once those conditions hold, enabling is an intentional reviewed code change that
removes the public-access requirement from retrieval indexing while preserving content
eligibility. Reconciliation/backfill then discovers newly eligible restricted documents
and performs their initial paid embedding. Existing public vectors remain reusable.

## Consequences

- The retrieval schema represents authorization from the start without overloading
  show-for scope.
- Until explicit enablement, no restricted content reaches the embedding provider or
  Elasticsearch; access fields are constant `public`/`[]` in indexed chunks.
- Direct source-document authorization is current and database-backed at read time.
- Access changes use the ordinary signal, hash, metadata-update, deletion, rerender,
  and reconciliation paths. There is no separate durable coordinator to operate.
- Under the current public-only policy, public-to-restricted changes evict rather than
  metadata-update the document.
- After restricted ingestion is enabled, access-only source changes normally preserve
  vectors; dependent rendered-body changes still require re-embedding.
- Revocation of content already rendered into another document is eventually
  consistent and has no hard completion SLA.
- The lexical search index remains public-only.

## Revisit this decision when

Any of the following invalidates the accepted-risk model:

- Per-tenant or per-customer isolation becomes real.
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

- **Keep retrieval permanently public-only.** Simpler, but it cannot eventually return
  useful group-restricted support material to authorized users.
- **Trust indexed group IDs without database revalidation.** Rejected because
  asynchronous ingestion inevitably creates stale direct-access metadata.
- **Add an enable flag now.** Rejected because it could send restricted content to the
  provider and index before policy approval and the secure reader exist.
- **Durable embargo plus ordered dependency-closure eviction.** Stronger immediate
  revocation, but deferred because it introduces new database state, synchronous
  closure capture, recovery, task coordination, and permanent operational burden for a
  tenant-isolation requirement that does not exist today.
- **Dependency-aware provenance on every chunk.** Could make rendered-fragment access
  enforceable at read time, but deferred until strict fragment-level revocation is a
  real requirement.
