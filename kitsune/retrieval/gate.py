"""Read-only comparison of what the database expects against what one index actually holds.

The gate never repairs. It is what a read swap is allowed to trust, so it has to be able to
fail for a reason an operator can act on, and it must not be able to hide a defect by fixing
it. ``verify_indexed_document`` is pure — the whole defect matrix is decided from expected
state plus stored state, with no Elasticsearch, Redis, or database access — and ``gate_index``
only enumerates and aggregates.

Findings carry categories, identities, and counts. They never carry article text, vectors,
credentials, or restriction group names or identifiers, because a gate report is the artefact
most likely to be pasted into a ticket.
"""

from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum

from elasticsearch.helpers import scan

from kitsune.retrieval.chunking import Chunk, chunk
from kitsune.retrieval.eligibility import eligible_documents, is_publicly_accessible
from kitsune.retrieval.embeddings import EmbeddingRecipe
from kitsune.retrieval.events import emit
from kitsune.retrieval.index import (
    PUBLIC_VISIBILITY,
    ChunkIdentity,
    ChunkSource,
    ExpectedDocumentState,
    IndexedDocumentState,
    access_metadata_matches,
    read_indexed_document,
    recipe_for_index,
)
from kitsune.retrieval.sync import CONTENT_TYPE, build_source, expected_state_for, is_usable_vector
from kitsune.search.es_utils import es_client
from kitsune.wiki.models import Document

MAX_REPORTED_FINDINGS = 200
DEFAULT_PAGE_SIZE = 500


class GateCategory(StrEnum):
    """Why one document or one indexed identity fails the gate.

    Deliberately bounded: these values are log fields and report keys, so the set has to stay
    small enough to aggregate on.
    """

    MISSING_DOCUMENT = "missing_document"
    MISSING_MANIFEST = "missing_manifest"
    STALE_MANIFEST = "stale_manifest"
    POSITION_GAP = "position_gap"
    ORPHAN_CHUNK = "orphan_chunk"
    INVALID_VECTOR = "invalid_vector"
    STALE_CHUNK_STATE = "stale_chunk_state"
    ACCESS_DRIFT = "access_drift"
    INELIGIBLE_IDENTITY = "ineligible_identity"
    DELETED_IDENTITY = "deleted_identity"


# Categories that mean "an eligible document needs re-syncing" rather than "this identity
# should not be in the index at all".
_REPAIRED_BY_SYNC = frozenset(
    {
        GateCategory.MISSING_DOCUMENT,
        GateCategory.MISSING_MANIFEST,
        GateCategory.STALE_MANIFEST,
        GateCategory.POSITION_GAP,
        GateCategory.ORPHAN_CHUNK,
        GateCategory.INVALID_VECTOR,
        GateCategory.STALE_CHUNK_STATE,
        GateCategory.ACCESS_DRIFT,
    }
)


@dataclass(frozen=True)
class GateFinding:
    category: GateCategory
    identity: ChunkIdentity
    # A short, bounded explanation. Never text, vectors, or group identifiers.
    detail: str = ""


@dataclass(frozen=True)
class GateReport:
    """One index's integrity snapshot.

    ``counts`` is exact even when ``findings`` is capped, and the two actionable sets are never
    capped — reconciliation dispatches from them.
    """

    index: str
    documents_checked: int = 0
    identities_indexed: int = 0
    counts: dict[str, int] = field(default_factory=dict)
    findings: tuple[GateFinding, ...] = ()
    findings_omitted: int = 0
    stale_document_ids: tuple[int, ...] = ()
    unexpected_identities: tuple[ChunkIdentity, ...] = ()

    @property
    def is_clean(self) -> bool:
        return not self.counts


def verify_indexed_document(
    *,
    chunks: list[Chunk],
    source: ChunkSource,
    expected_state: ExpectedDocumentState,
    indexed: IndexedDocumentState,
    recipe: EmbeddingRecipe,
) -> tuple[GateFinding, ...]:
    """Every way one document's stored state can disagree with what the database implies.

    Reports all findings rather than the first, because an operator deciding whether to promote
    a generation needs the shape of the damage, not one example of it.
    """
    identity = source.identity
    findings: list[GateFinding] = []
    if source.visibility != PUBLIC_VISIBILITY or source.access_group_ids:
        findings.append(
            GateFinding(
                GateCategory.ACCESS_DRIFT,
                identity,
                "indexed while the database restricts it",
            )
        )
    else:
        drifted = sum(not access_metadata_matches(stored, source) for stored in indexed.chunks)
        if drifted:
            findings.append(
                GateFinding(
                    GateCategory.ACCESS_DRIFT,
                    identity,
                    f"{drifted} of {len(indexed.chunks)} chunks disagree with the database",
                )
            )

    if indexed.manifest is None and not indexed.chunks:
        findings.append(GateFinding(GateCategory.MISSING_DOCUMENT, identity, "nothing indexed"))
        return tuple(findings)
    if indexed.manifest is None:
        findings.append(
            GateFinding(GateCategory.MISSING_MANIFEST, identity, "chunks without a manifest")
        )
    elif indexed.manifest != expected_state:
        findings.append(
            GateFinding(
                GateCategory.STALE_MANIFEST, identity, "manifest is not the expected state"
            )
        )

    by_position = {stored.get("position"): stored for stored in indexed.chunks}
    duplicate_positions = len(indexed.chunks) - len(by_position)
    expected_positions = set(range(len(chunks)))
    if missing := sorted(expected_positions - set(by_position)):
        findings.append(
            GateFinding(GateCategory.POSITION_GAP, identity, f"{len(missing)} positions absent")
        )
    orphans = sorted(set(by_position) - expected_positions, key=str)
    if orphans or duplicate_positions:
        findings.append(
            GateFinding(
                GateCategory.ORPHAN_CHUNK,
                identity,
                f"{len(orphans) + duplicate_positions} unexpected or duplicate positions",
            )
        )

    unusable = 0
    stale = 0
    for item in chunks:
        stored = by_position.get(item.position)
        if stored is None:
            continue
        if not is_usable_vector(stored.get("content_vector"), recipe):
            unusable += 1
        stored_text = stored.get("content_text")
        if (
            not isinstance(stored_text, dict)
            or stored_text.get(source.locale) != item.text
            or stored.get("content_hash") != expected_state.content_hash
            or stored.get("index_state_hash") != expected_state.index_state_hash
            or stored.get("chunking_generation") != expected_state.chunking_generation
        ):
            stale += 1
    if unusable:
        findings.append(
            GateFinding(
                GateCategory.INVALID_VECTOR, identity, f"{unusable} chunks have unusable vectors"
            )
        )
    if stale:
        findings.append(
            GateFinding(
                GateCategory.STALE_CHUNK_STATE,
                identity,
                f"{stale} chunks disagree with the commit",
            )
        )
    return tuple(findings)


def _indexed_identities(index: str, locales: tuple[str, ...]) -> set[ChunkIdentity]:
    """Every identity present in one index, scanned rather than paged by hit limit.

    Vectors are deliberately excluded here: this pass exists to find identities, and holding a
    whole corpus of vectors in memory to do it would be the difference between a command that
    runs and one that does not.
    """
    filters: list[dict] = [{"term": {"content_type": CONTENT_TYPE}}]
    if locales:
        filters.append({"terms": {"locale": list(locales)}})
    hits = scan(
        es_client(),
        index=index,
        query={
            "query": {"bool": {"filter": filters}},
            "_source": ["content_type", "object_id", "locale"],
        },
    )
    return {
        ChunkIdentity(
            content_type=hit["_source"]["content_type"],
            object_id=hit["_source"]["object_id"],
            locale=hit["_source"]["locale"],
        )
        for hit in hits
    }


def gate_index(
    index: str,
    *,
    locales=(),
    page_size: int | None = None,
    max_findings: int = MAX_REPORTED_FINDINGS,
) -> GateReport:
    """Compare one concrete index against the database in both directions, writing nothing.

    Both directions matter and neither implies the other: an eligible document can be missing
    from the index, and an identity can sit in the index with nothing eligible behind it. A
    read swap gated on only the first would promote a generation still serving withdrawn
    content.
    """
    if isinstance(locales, str | bytes):
        raise TypeError("locales must be a sequence of locale strings")
    locales = tuple(dict.fromkeys(locales))
    if any(not isinstance(locale, str) or not locale for locale in locales):
        raise ValueError("locales must contain non-empty strings")
    if page_size is None:
        page = DEFAULT_PAGE_SIZE
    elif not isinstance(page_size, int) or isinstance(page_size, bool) or page_size <= 0:
        raise ValueError("page_size must be a positive integer")
    else:
        page = page_size
    if not isinstance(max_findings, int) or isinstance(max_findings, bool) or max_findings < 0:
        raise ValueError("max_findings must be a non-negative integer")
    recipe = recipe_for_index(index)
    remaining = _indexed_identities(index, locales)
    identities_indexed = len(remaining)

    counts: Counter[str] = Counter()
    reported: list[GateFinding] = []
    omitted = 0
    stale_document_ids: list[int] = []
    documents_checked = 0

    def record(finding: GateFinding) -> None:
        nonlocal omitted
        counts[finding.category.value] += 1
        if len(reported) < max_findings:
            reported.append(finding)
        else:
            omitted += 1

    documents = eligible_documents()
    if locales:
        documents = documents.filter(locale__in=locales)
    for document in documents.order_by("pk").iterator(chunk_size=page):
        documents_checked += 1
        identity = ChunkIdentity(CONTENT_TYPE, str(document.id), document.locale)
        remaining.discard(identity)
        source = build_source(document)
        chunks = chunk(CONTENT_TYPE, document.html, title=document.title)
        findings = verify_indexed_document(
            chunks=chunks,
            source=source,
            expected_state=expected_state_for(chunks, source, document),
            indexed=read_indexed_document(index=index, identity=identity),
            recipe=recipe,
        )
        if any(finding.category in _REPAIRED_BY_SYNC for finding in findings):
            stale_document_ids.append(document.id)
        for finding in findings:
            record(finding)

    unexpected = sorted(remaining, key=lambda item: (item.object_id, item.locale))
    for start in range(0, len(unexpected), page):
        batch = unexpected[start : start + page]
        rows = (
            Document.objects.select_related("parent")
            .prefetch_related("restrict_to_groups", "parent__restrict_to_groups")
            .in_bulk([int(item.object_id) for item in batch])
        )
        for identity in batch:
            document = rows.get(int(identity.object_id))
            if document is None:
                finding = GateFinding(
                    GateCategory.DELETED_IDENTITY, identity, "source row no longer exists"
                )
            elif not is_publicly_accessible(document):
                finding = GateFinding(
                    GateCategory.ACCESS_DRIFT,
                    identity,
                    "indexed while the database restricts it",
                )
            else:
                finding = GateFinding(
                    GateCategory.INELIGIBLE_IDENTITY,
                    identity,
                    "source row is not retrieval-eligible",
                )
            record(finding)

    report = GateReport(
        index=index,
        documents_checked=documents_checked,
        identities_indexed=identities_indexed,
        counts=dict(counts),
        findings=tuple(reported),
        findings_omitted=omitted,
        stale_document_ids=tuple(stale_document_ids),
        unexpected_identities=tuple(unexpected),
    )
    emit(
        "retrieval.gate.completed",
        index=index,
        clean=report.is_clean,
        documents_checked=documents_checked,
        identities_indexed=identities_indexed,
        counts=report.counts,
        findings_omitted=omitted,
    )
    return report
