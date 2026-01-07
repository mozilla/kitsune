import re
from typing import Any

from django.conf import settings

from kitsune.llm.l10n.config import L10N_LLM_MODEL
from kitsune.llm.l10n.prompt import (
    DEFAULT_ANCHOR_MAP_RESULT,
    AnchorMapResult,
    anchor_map_parser,
    anchor_map_prompt,
    translation_parser,
    translation_prompt,
)
from kitsune.llm.utils import build_chain_with_retry, get_llm
from kitsune.wiki.models import Document, RevisionAnchorRecord

# Matches internal anchor links: [[#w_anchor_name|optional text]]
INTERNAL_ANCHOR_REGEX = re.compile(r"\[\[\s*#w_[a-z0-9\-_]+?\s*(\|.*?)?\]\]")
# Matches external anchor links: [[ArticleTitle#w_anchor_name|optional text]]
# Excludes special prefixes like Image:, Video:, Template:, etc.
EXTERNAL_ANCHOR_REGEX = re.compile(
    r"\[\[\s*(?!Image:|Video:|V:|Button:|UI:|Include:|I:|Template:|T:)"
    r"(?P<title>[^#|\]]+?)#(?P<anchor>w_[a-z0-9\-_]+?)\s*(\|.*?)?\]\]"
)


def translate(doc: Document, target_locale: str) -> dict[str, dict[str, Any]]:
    """
    Translates the summary, keywords, content, and, conditionally, the title of the
    given document into the target locale. The given document must be a parent
    document.
    """
    llm = get_llm(model_name=L10N_LLM_MODEL, temperature=0.0)

    translation_chain = translation_prompt | llm | translation_parser

    payload: dict[str, Any] = {
        "source_language": settings.LOCALES[doc.locale].english,
        "target_language": settings.LOCALES[target_locale].english,
    }

    result: dict[str, dict[str, Any]] = {}

    content_attributes = ["summary", "keywords", "content"]

    target_doc = doc.translated_to(target_locale)

    # Generate a translation of the title only if the doc is not a template
    # and it doesn't already have a child in the target locale.
    if not doc.is_template and not target_doc:
        content_attributes.append("title")

    def get_source_text(content_attribute):
        if content_attribute == "title":
            return doc.title
        return getattr(doc.latest_localizable_revision, content_attribute)

    def get_prior_translation(content_attribute):
        if (
            content_attribute != "title"
            and target_doc
            and (target_rev := target_doc.current_revision)
            and (source_rev := target_rev.based_on)
            and (source_text := getattr(source_rev, content_attribute))
            and (target_text := getattr(target_rev, content_attribute))
        ):
            return {"source_text": source_text, "target_text": target_text}
        return None

    for content_attribute in content_attributes:
        payload.update(
            source_text=get_source_text(content_attribute),
            prior_translation=get_prior_translation(content_attribute),
        )

        if payload["source_text"]:
            result[content_attribute] = translation_chain.invoke(payload)

            if content_attribute == "content":
                result["content"]["translation"] = resolve_anchors(
                    source_locale=doc.locale,
                    source_content=payload["source_text"],
                    target_locale=target_locale,
                    target_content=result["content"]["translation"],
                )
        else:
            result[content_attribute] = {
                "translation": "",
                "explanation": (
                    "No translation was necessary. The source text was an empty string."
                ),
            }

    return result


def resolve_anchors(
    source_locale: str, source_content: str, target_locale: str, target_content: str
) -> str:
    """
    Resolves both internal and external anchor references in translated wiki content.

    When content is machine-translated, anchor IDs (like #w_section_name) are generated
    from translated heading text and may differ from the source locale. This function
    updates anchor references in the translated content to point to the correct
    locale-specific anchor IDs.

    Args:
        source_locale: The locale code of the source content (e.g., "en-US").
        source_content: The original wiki markup content before translation.
        target_locale: The locale code of the target translation (e.g., "fr").
        target_content: The translated wiki markup content with outdated anchor references.

    Returns:
        The target content with all anchor references updated to match the target locale.
    """
    target_content = resolve_internal_anchors(
        source_locale, source_content, target_locale, target_content
    )
    return resolve_external_anchors(source_locale, source_content, target_locale, target_content)


def resolve_internal_anchors(
    source_locale: str, source_content: str, target_locale: str, target_content: str
) -> str:
    """
    Resolves internal anchor references (links within the same document).

    Internal anchors use the syntax [[#w_anchor_name|optional text]]. When headings are
    translated, their generated anchor IDs change. This function uses an LLM to map
    source anchor IDs to their translated equivalents and updates all references.

    Args:
        source_locale: The locale code of the source content.
        source_content: The original wiki markup content.
        target_locale: The locale code of the target translation.
        target_content: The translated wiki markup content.

    Returns:
        The target content with internal anchor references updated. If no internal
        anchors are found in the source content, returns target_content unchanged.
    """
    if not (
        source_locale
        and target_locale
        and target_content
        and INTERNAL_ANCHOR_REGEX.search(source_content)
    ):
        return target_content

    from kitsune.wiki.parser import wiki_to_html

    source_html = wiki_to_html(source_content, locale=source_locale)
    target_html = wiki_to_html(target_content, locale=target_locale)

    anchor_map_result = get_anchor_map(source_locale, source_html, target_locale, target_html)
    anchor_map = anchor_map_result["map"]

    if source_anchors := {
        source_anchor
        for source_anchor, target_anchor in anchor_map.items()
        if target_anchor != source_anchor
    }:
        # Perform the replacements in one pass, in order to avoid the
        # possibility of later replacements affecting earlier replacements.

        def resolve_anchor(mo: re.Match) -> str:
            source_anchor = mo.group(2)
            return f"{mo.group(1)}{anchor_map.get(source_anchor, source_anchor)}{mo.group(3)}"

        target_content = re.sub(
            rf"(\[\[\s*#)({'|'.join(re.escape(sa) for sa in source_anchors)})(\s|\||])",
            resolve_anchor,
            target_content,
        )

    return target_content


def resolve_external_anchors(
    source_locale: str, source_content: str, target_locale: str, target_content: str
) -> str:
    """
    Resolves external anchor references (links to sections in other documents).

    External anchors use the syntax [[ArticleTitle#w_anchor_name|optional text]].
    This function handles both the article title translation and anchor ID updates
    for references to other wiki documents.

    If a human has already translated an article title in the content but left the
    anchor unchanged, that case will be handled by updating only the anchor.

    Args:
        source_locale: The locale code of the source content.
        source_content: The original wiki markup content.
        target_locale: The locale code of the target translation.
        target_content: The translated wiki markup content.

    Returns:
        The target content with external anchor references updated. If no external
        anchors are found in the source content, or if referenced articles don't have
        translations in the target locale, returns target_content unchanged.
    """
    if not (
        source_locale
        and target_locale
        and target_content
        and EXTERNAL_ANCHOR_REGEX.search(source_content)
    ):
        return target_content

    external_anchors_by_title: dict[str, set[str]] = {}
    for mo in EXTERNAL_ANCHOR_REGEX.finditer(source_content):
        if mo and (title := mo.group("title")) and (anchor := mo.group("anchor")):
            external_anchors_by_title.setdefault(title, set()).add(anchor)

    # Get the translations of all of the external article titles in a single query.
    external_translations = {
        translation.parent.title: translation
        for translation in Document.objects.filter(
            locale=target_locale,
            current_revision__isnull=False,
            parent__title__in=external_anchors_by_title.keys(),
        ).select_related(
            "parent",
            "current_revision",
            "current_revision__based_on",
            "current_revision__anchor_record",
        )
    }

    for title, anchors in external_anchors_by_title.items():
        # We only need to consider external anchors with a translation.
        if not (anchors and (external_translation := external_translations.get(title))):
            continue

        current_rev = external_translation.current_revision
        # Use the stored anchor map if available.
        if (anchor_map := current_rev.anchor_map) is None:
            # Otherwise, we need to build the anchor mapping.
            if current_rev.based_on_id == external_translation.parent.current_revision_id:
                source_html = external_translation.parent.html
            else:
                source_html = current_rev.based_on.content_parsed

            anchor_map_result = get_anchor_map(
                source_locale, source_html, target_locale, external_translation.html
            )

            if not anchor_map_result["map"]:
                # If the map is empty, something is wrong,
                # so move on without recording the result.
                continue

            anchor_record, _ = RevisionAnchorRecord.objects.get_or_create(
                revision=current_rev, defaults=anchor_map_result
            )
            anchor_map = anchor_record.map

        # Perform the replacements in one pass, in order to avoid the
        # possibility of later replacements affecting earlier replacements.

        def resolve_anchor(mo: re.Match) -> str:
            source_anchor = mo.group(3)
            return (
                f"{mo.group(1)}{external_translation.title}#"
                f"{anchor_map.get(source_anchor, source_anchor)}{mo.group(4)}"
            )

        target_content = re.sub(
            (
                rf"(\[\[\s*)({re.escape(title)}|{re.escape(external_translation.title)})"
                rf"#({'|'.join(re.escape(sa) for sa in anchors)})(\s|\||])"
            ),
            resolve_anchor,
            target_content,
        )

    return target_content


def get_anchor_map(
    source_locale: str, source_html: str, target_locale: str, target_html: str
) -> AnchorMapResult:
    """
    Uses an LLM to generate a mapping between source and target anchor IDs.

    This function analyzes rendered HTML from both source and target locales to identify
    corresponding heading sections and their anchor IDs. The LLM matches headings based
    on semantic meaning rather than exact text, making it robust to translation variations.

    Args:
        source_locale: The locale code of the source content.
        source_html: The rendered HTML of the source content with anchor IDs.
        target_locale: The locale code of the target content.
        target_html: The rendered HTML of the target content with anchor IDs.

    Returns:
        AnchorMapResult: A TypedDict containing "map" and "explanation" keys.
        The value of the "map" key is a dict that maps source anchor IDs to
        their corresponding target anchor IDs. For example:
            {"map": {"w_files": "w_archivos", ...}, "explanation": "..."}
    """
    llm = get_llm(model_name=L10N_LLM_MODEL, temperature=0.0)

    anchor_map_chain = build_chain_with_retry(
        anchor_map_prompt, llm, anchor_map_parser, default_result=DEFAULT_ANCHOR_MAP_RESULT
    )

    payload: dict[str, Any] = {
        "source_html": source_html,
        "target_html": target_html,
        "source_language": settings.LOCALES[source_locale].english,
        "target_language": settings.LOCALES[target_locale].english,
    }

    return anchor_map_chain.invoke(payload)
