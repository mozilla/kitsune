"""Read-only comparison of database truth with promotion-critical indexed state.

The gate never repairs. One bounded Elasticsearch scan loads manifests, positions, and access
metadata for the corpus; article text and vectors are deliberately excluded. The database
walk then compares each eligible document and classifies identities left only in the index.

Findings carry categories, identities, and counts. They never carry article text, vectors,
credentials, or restriction group names or identifiers, because a gate report is the artefact
most likely to be pasted into a ticket.
"""

from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum

from kitsune.retrieval.chunking import chunk
from kitsune.retrieval.eligibility import eligible_documents, is_publicly_accessible
from kitsune.retrieval.events import emit
from kitsune.retrieval.index import (
    ChunkIdentity,
    ChunkSource,
    ExpectedDocumentState,
    IndexedDocumentSummary,
    access_metadata_matches,
    chunk_layout_matches,
    read_index_summaries,
)
from kitsune.retrieval.sync import CONTENT_TYPE, build_source, expected_state_for
from kitsune.retrieval.validation import is_nonnegative_int, is_positive_int
from kitsune.search.es_utils import es_client
from kitsune.wiki.models import Document

MAX_REPORTED_FINDINGS = 200
DEFAULT_PAGE_SIZE = 500


class GateCategory(StrEnum):
    """Why one document or one indexed identity fails the gate.

    Deliberately bounded: these values are log fields and report keys, so the set has to stay
    small enough to aggregate on.
    """

    STALE_DOCUMENT = "stale_document"
    CHUNK_LAYOUT_MISMATCH = "chunk_layout_mismatch"
    ACCESS_DRIFT = "access_drift"
    UNEXPECTED_IDENTITY = "unexpected_identity"


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
    source: ChunkSource,
    expected_state: ExpectedDocumentState,
    indexed: IndexedDocumentSummary,
) -> tuple[GateFinding, ...]:
    """Compare one eligible document without reading its stored text or vectors.

    Reports all findings rather than the first, because an operator deciding whether to promote
    a generation needs the shape of the damage, not one example of it.
    """
    identity = source.identity
    findings: list[GateFinding] = []
    drifted = sum(not access_metadata_matches(stored, source) for stored in indexed.chunks)
    if drifted:
        findings.append(
            GateFinding(
                GateCategory.ACCESS_DRIFT,
                identity,
                f"{drifted} of {len(indexed.chunks)} chunks disagree with the database",
            )
        )

    if indexed.manifest is None:
        findings.append(
            GateFinding(GateCategory.STALE_DOCUMENT, identity, "committed manifest is missing")
        )
    elif indexed.manifest != expected_state:
        findings.append(
            GateFinding(
                GateCategory.STALE_DOCUMENT, identity, "manifest is not the expected state"
            )
        )

    if indexed.manifest is not None and not chunk_layout_matches(
        indexed.chunks, expected_state.chunk_count
    ):
        findings.append(
            GateFinding(
                GateCategory.CHUNK_LAYOUT_MISMATCH,
                identity,
                "stored positions do not match the expected chunk layout",
            )
        )
    return tuple(findings)


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
    elif not is_positive_int(page_size):
        raise ValueError("page_size must be a positive integer")
    else:
        page = page_size
    if not is_nonnegative_int(max_findings):
        raise ValueError("max_findings must be a non-negative integer")
    # Gate findings drive promotion and reconciliation; they must describe the current
    # index, not the last refresh. These scans are operator-run or daily, never per-write.
    es_client().indices.refresh(index=index)
    remaining = read_index_summaries(index=index, content_type=CONTENT_TYPE, locales=locales)
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
        source = build_source(document)
        chunks = chunk(CONTENT_TYPE, document.html, title=document.title)
        findings = verify_indexed_document(
            source=source,
            expected_state=expected_state_for(chunks, source, document),
            indexed=remaining.pop(identity, IndexedDocumentSummary(None, ())),
        )
        if findings:
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
                    GateCategory.UNEXPECTED_IDENTITY, identity, "source row no longer exists"
                )
            elif not is_publicly_accessible(document):
                finding = GateFinding(
                    GateCategory.ACCESS_DRIFT,
                    identity,
                    "indexed while the database restricts it",
                )
            else:
                finding = GateFinding(
                    GateCategory.UNEXPECTED_IDENTITY,
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
