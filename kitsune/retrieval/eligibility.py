"""Retrieval eligibility predicates, the equivalent queryset, and access metadata.

``eligible_documents()`` must stay provably equal to ``is_retrieval_indexable`` (see
``tests/test_eligibility.py``) so incremental, backfill, and reconciliation paths select
the same documents. Eligibility is content-only: private articles are ingested with their
access metadata and filtered at read time (ADR 0006).
"""

from django.contrib.auth.models import Group
from django.db.models import Prefetch, Q, QuerySet

from kitsune.retrieval.index import PUBLIC_VISIBILITY, RESTRICTED_VISIBILITY
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.wiki.indexing import EXCLUDED_CATEGORIES, is_indexable_content
from kitsune.wiki.models import Audience, Document

PREFETCHED_GROUPS = "prefetched_groups"


def is_retrieval_indexable(document) -> bool:
    """Whether the document is ingested: approved, supported KB content, whatever its audiences."""
    return document.current_revision_id is not None and is_indexable_content(document)


def content_eligible_documents(
    queryset: QuerySet[Document] | None = None,
) -> QuerySet[Document]:
    """Apply the queryset equivalent of ``is_retrieval_indexable``, without prefetches."""
    queryset = Document.objects.all() if queryset is None else queryset
    return queryset.filter(current_revision__isnull=False).exclude(
        Q(html__startswith=REDIRECT_HTML)
        | Q(is_template=True)
        | Q(is_archived=True)
        | Q(category__in=EXCLUDED_CATEGORIES)
    )


def audience_prefetches() -> list[Prefetch]:
    """Prefetch the audiences of a document and of its parent, with their group ids.

    Batch paths use these so ``access_group_ids_for`` costs no query per private document. The
    ids sit in a ``to_attr`` list because the pre-commit hook rejects reading an audience's
    groups through its manager.
    """
    return [
        Prefetch(
            lookup,
            queryset=Audience.objects.prefetch_related(
                Prefetch("groups", queryset=Group.objects.only("id"), to_attr=PREFETCHED_GROUPS)
            ),
        )
        for lookup in ("audiences", "parent__audiences")
    ]


def eligible_documents() -> QuerySet[Document]:
    """The queryset equivalent of ``is_retrieval_indexable``, proven equal in tests.

    Translations are included on their own current revision. The excludes mirror
    ``is_indexable_content`` on the document's own (parent-synced) fields.
    """
    return (
        content_eligible_documents()
        .select_related("parent", "current_revision")
        .prefetch_related(
            "topics",
            "products",
            "parent__topics",
            "parent__products",
            *audience_prefetches(),
        )
    )


def family_id_for(document) -> int:
    """The original document id used in the cross-lingual KB family key."""
    return document.parent_id or document.id


def access_group_ids_for(document) -> list[int]:
    """Sorted, unique group ids of the original's audiences; none for a public document."""
    if not document.is_restricted:
        return []
    original = document.original
    audiences = list(original.audiences.all())
    if all(hasattr(audience, PREFETCHED_GROUPS) for audience in audiences):
        return sorted(
            {group.id for audience in audiences for group in getattr(audience, PREFETCHED_GROUPS)}
        )
    return sorted(
        set(original.audiences.filter(groups__isnull=False).values_list("groups", flat=True))
    )


def visibility_for(document) -> str:
    return RESTRICTED_VISIBILITY if document.is_restricted else PUBLIC_VISIBILITY
