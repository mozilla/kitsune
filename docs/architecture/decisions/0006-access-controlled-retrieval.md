# 6 - Access-controlled retrieval for group-restricted KB content

Date: 2026-07-28

## Status

Proposed — pending restricted-content policy approval.

Until this decision is accepted, retrieval ingestion remains public-only:
restricted content must not be sent to the embedding provider or stored in the
retrieval index. The access fields and public-only policy boundary described below
may be modeled while inert, but there is no runtime switch that can enable
restricted ingestion.

## Context

Kitsune knowledge-base documents can be restricted to one or more Django
authentication groups. A document passes the group-access check when it is
unrestricted, the caller belongs to any allowed group, or the caller is a
superuser or a member of Kitsune's staff group. Translations inherit the
restrictions of their original document.

The retrieval layer turns approved, rendered KB HTML into chunks, sends each
chunk's text to a managed embedding provider, and stores the text, vector, and
metadata in Elasticsearch. It currently indexes public content only. The desired
future behavior is for an authenticated caller to retrieve both public content and
restricted content that caller may view. The existing lexical `WikiDocument`
index remains public-only.

This is not merely an Elasticsearch filter:

- Elasticsearch is updated asynchronously and can contain stale access metadata.
- A document's restrictions affect which templates and includes the wiki parser
  may render into its stored HTML.
- Changing the restrictions of an included document can therefore affect other
  documents whose own access rules did not change.
- Restricted text would be processed by the embedding provider and stored in the
  retrieval cluster, which requires explicit policy approval.

The anticipated material is embargoed or pre-launch support content rather than a
general secrets store. That classification does not itself authorize external
processing or indexed storage.

## Decision

### Model access independently from show-for scope

Every retrieval chunk and its `ChunkSource` carry two keyword fields:

```python
access_group_ids = sorted(
    document.original.restrict_to_groups.values_list("id", flat=True)
)
visibility = "group_restricted" if access_group_ids else "public"
```

`access_group_ids` uses canonical, sorted integer group IDs. Translations read the
IDs from `document.original`. The fields are included in `index_state_hash`, so an
access-metadata change is detectable without changing `content_hash` or
re-embedding unchanged text.

The per-document manifest stores `index_state_hash`, not a duplicate copy of the
group list. `visibility` is deliberately distinct from the chunker's `scope`,
which represents show-for applicability rather than authorization.

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

There is no `include_restricted` argument or configuration flag. Enabling
restricted ingestion later is a deliberate code change to the object predicate,
queryset, reconciliation expectations, and tests; it cannot happen through an
environment toggle.

The lexical index keeps its existing, behavior-preserving public-only predicate.
Its merged-locale representation is separate from the retrieval index, which
stores one source document per locale.

### Serialize restriction changes through a security-first workflow

A restriction change is not assumed to be metadata-only. The affected set includes:

- the changed document and its translations; and
- every document that directly or transitively renders it as a template or include,
  including those documents' relevant translations.

Restriction mutations must capture and durably embargo the complete affected set in
the same database transaction as the mutation, then schedule one ordered workflow
after that transaction commits:

1. Snapshot the full render-affected dependency closure before rerendering changes
   its dependency records, and persist the embargo before commit. Traversal and inserts
   may be batched, but a size threshold must never truncate the security boundary.
2. Prevent ordinary ingestion from repopulating those identities with pre-render
   HTML. The durable embargo is the security fence; ephemeral ingestion locks may be
   acquired in bounded batches for execution serialization.
3. Evict the affected identities from every active physical retrieval index and
   verify the deletions.
4. Rerender the affected documents.
5. Let each resulting `Document.save()` schedule ordinary hash-gated ingestion.
   Re-embed only where the freshly rendered `content_hash` changed.

Independent eviction and rendering tasks are insufficient because Celery does not
guarantee their relative execution order. If eviction or rendering fails, the
affected retrieval content remains absent; temporary absence is preferable to
serving content under stale restrictions.

There is also a bounded interval between the database commit and asynchronous
eviction. Rechecking only the containing document cannot close this interval when
its stale rendered HTML contains material from a newly restricted dependency. A
production reader must therefore consult an access-change embargo for the affected
closure whenever eviction remains asynchronous, or restriction changes must use
synchronous verified eviction before becoming visible. This protection is an
enablement prerequisite, not an optional optimization.

### Treat Elasticsearch filtering as defense in depth

The retrieval caller's identity and group IDs are derived server-side from the
authenticated user, never accepted as caller-supplied group IDs.

For a caller without the staff/superuser bypass, Elasticsearch pre-filters
candidates using:

```text
visibility = public
OR
(visibility = group_restricted AND access_group_ids intersects caller_group_ids)
```

Before a hit is returned or its text is placed in a chatbot prompt, the application
batch-loads the source documents and revalidates both:

- current content eligibility, including the approved/current revision; and
- current authorization for the caller.

It fetches additional candidates as necessary to replace rejected stale hits.
Elasticsearch filtering protects recall and reduces exposure inside the application,
but the authoritative database check remains the authorization boundary.

Retrieval results, generated answers, and related caches must either contain public
content only or be keyed and revalidated against the caller's authorization. A
restricted result or generated answer must never be reused across callers solely
because their query text matches.

Changing a user's group membership does not require document reindexing: queries
use current server-side membership and the database recheck remains authoritative.

### Gate enablement on policy and the secure reader

Restricted ingestion may be enabled only after both conditions hold:

1. The restricted-content policy owner approves processing and storage. Approval
   must cover the embedding provider and Elasticsearch, including retention,
   regional/data-handling requirements, backups, and operator access.
2. The group-aware reader, authoritative eligibility/access revalidation,
   permission-aware caching, and ordered restriction-change workflow above are
   implemented and tested.

Once those conditions hold, enabling is an intentional reviewed code change that
removes the public-access requirement from retrieval indexing while preserving
content eligibility. Reconciliation/backfill then discovers newly eligible
restricted documents and performs their initial paid embedding. Existing public
documents do not need re-embedding merely because access fields become active.

## Consequences

- The retrieval schema represents authorization from the start without overloading
  show-for scope.
- Until enablement, no restricted content reaches the embedding provider or
  Elasticsearch; the new fields are constant `public`/`[]` in indexed chunks.
- Access-list changes normally use the metadata-only index path after safe
  rerendering, but a rendered-body change still requires re-embedding.
- Newly enabled restricted documents require a paid initial embedding backfill;
  already-indexed public vectors remain reusable.
- Every personalized retrieval request carries a server-derived group filter and
  an authoritative database recheck.
- Restriction changes require dependency-closure eviction and ordered coordination,
  not only a translation-family refresh.
- Capturing the complete dependency closure adds synchronous work to restriction and
  deletion mutations. Closure size/capture latency must be observable and large
  fan-out should alert, but partial capture is not an acceptable latency optimization.
- The lexical search index remains public-only.

## Alternatives rejected

- **Keep retrieval permanently public-only.** Simpler, but it cannot return useful
  group-restricted support material to authorized users.
- **Retrieve broadly and filter only after Elasticsearch.** Secure only if the
  database check is flawless, but inaccessible documents can consume the top
  candidates and hide relevant accessible results.
- **Trust indexed group IDs without database revalidation.** Rejected because
  asynchronous ingestion inevitably creates stale-access windows.
- **Add an enable flag now.** Rejected because it could send restricted content to
  the provider and index before the secure reader and policy approval exist.
