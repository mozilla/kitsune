"""Retrieval eligibility predicates, the equivalent queryset, and access metadata.

``eligible_documents()`` must stay provably equal to ``is_retrieval_indexable`` (see
``tests/test_eligibility.py``) so incremental, backfill, and reconciliation paths select
the same documents. The current rollout is public-only and hardcoded — there is no
``include_restricted`` flag; enabling restricted ingestion is a deliberate later code
change (ADR 0006).
"""

from django.db.models import Q, QuerySet

from kitsune.retrieval.index import PUBLIC_VISIBILITY, RESTRICTED_VISIBILITY
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.wiki.indexing import EXCLUDED_CATEGORIES, is_indexable_content
from kitsune.wiki.models import Document


def is_retrieval_content_eligible(document) -> bool:
    """Approved, supported KB content, independent of access."""
    return document.current_revision_id is not None and is_indexable_content(document)


def is_publicly_accessible(document) -> bool:
    """Whether the document is unrestricted (translations inherit from their original)."""
    return not document.is_restricted


def is_retrieval_indexable(document) -> bool:
    """The current public-only ingestion policy — hardcoded, no ``include_restricted``."""
    return is_retrieval_content_eligible(document) and is_publicly_accessible(document)


def eligible_documents() -> QuerySet[Document]:
    """The queryset equivalent of ``is_retrieval_indexable``, proven equal in tests.

    ``visible()`` (no viewer) enforces ``current_revision`` and unrestricted access,
    including a translation's inherited restriction via its parent. The excludes mirror
    ``is_indexable_content`` on the document's own (parent-synced) fields.
    """
    return (
        Document.objects.visible()
        .exclude(
            Q(html__startswith=REDIRECT_HTML)
            | Q(is_template=True)
            | Q(is_archived=True)
            | Q(category__in=EXCLUDED_CATEGORIES)
        )
        .select_related("parent", "current_revision")
        .prefetch_related(
            "topics",
            "products",
            "restrict_to_groups",
            "parent__topics",
            "parent__products",
            "parent__restrict_to_groups",
        )
    )


def family_id_for(document) -> int:
    """The original document id used in the cross-lingual KB family key."""
    return document.parent_id or document.id


def family_documents(document) -> QuerySet[Document]:
    """The original document and all of its translations."""
    original_id = family_id_for(document)
    return Document.objects.filter(Q(pk=original_id) | Q(parent_id=original_id))


def family_document_ids(document) -> list[int]:
    return list(family_documents(document).values_list("id", flat=True))


def access_group_ids_for(document) -> list[int]:
    """Sorted restriction group ids from the original (translations inherit)."""
    return sorted(group.id for group in document.original.restrict_to_groups.all())


def visibility_for(document) -> str:
    return RESTRICTED_VISIBILITY if access_group_ids_for(document) else PUBLIC_VISIBILITY
