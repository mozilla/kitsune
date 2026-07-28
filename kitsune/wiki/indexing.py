"""Content-type exclusions shared by the lexical (``WikiDocument``) and retrieval indexes.

Extracted once so the two indexing paths cannot drift. Access (restriction) and
approval (``current_revision``) are deliberately *not* decided here; each index applies
those on top of this shared content-type rule.
"""

from kitsune.wiki.config import (
    ADMINISTRATION_CATEGORY,
    CANNED_RESPONSES_CATEGORY,
    REDIRECT_HTML,
    TEMPLATES_CATEGORY,
)

EXCLUDED_CATEGORIES = frozenset(
    {TEMPLATES_CATEGORY, CANNED_RESPONSES_CATEGORY, ADMINISTRATION_CATEGORY}
)


def is_indexable_content(document) -> bool:
    """Whether a document is a supported content *type* for any index.

    Access- and revision-agnostic. ``is_template`` is checked explicitly in addition to
    the template category so a row left inconsistent by a parent leaving the template
    category — where ``_ensure_inherited_attr("category")`` bulk-updates translations
    without re-running ``save()`` — fails closed.
    """
    return not (
        document.html.startswith(REDIRECT_HTML)
        or document.is_template
        or document.is_archived
        or document.category in EXCLUDED_CATEGORIES
    )


def is_public_indexing_allowed(document) -> bool:
    """The lexical (``WikiDocument``) rule: indexable content that is not restricted.

    ``current_revision`` is intentionally excluded — the bulk ``visible()`` queryset and
    the document-save signal enforce it, and discarding a revision-less translation in
    ``WikiDocument.prepare`` could unindex the whole merged-locale family under the
    parent's ES id.
    """
    return is_indexable_content(document) and not document.is_restricted
