from typing import TYPE_CHECKING, Any

from django.conf import settings

from kitsune.llm.l10n.prompt import translation_parser, translation_prompt
from kitsune.llm.l10n.config import L10N_LLM_MODEL
from kitsune.llm.utils import get_llm

if TYPE_CHECKING:
    from kitsune.wiki.models import Document


def translate(doc: "Document", target_locale: str) -> dict[str, dict[str, Any]]:
    """
    Translates the summary, keywords, content, and, conditionally, the title of the
    given document into the target locale. The given document must be a parent
    document.
    """
    llm = get_llm(model_name=L10N_LLM_MODEL)

    translation_chain = translation_prompt | llm | translation_parser

    payload: dict[str, Any] = dict(
        source_language=settings.LOCALES[doc.locale].english,
        target_language=settings.LOCALES[target_locale].english,
    )

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
        ):
            return dict(
                source_text=getattr(source_rev, content_attribute),
                target_text=getattr(target_rev, content_attribute),
            )
        return None

    for content_attribute in content_attributes:

        payload.update(
            source_text=get_source_text(content_attribute),
            prior_translation=get_prior_translation(content_attribute),
        )

        result[content_attribute] = translation_chain.invoke(payload)

    return result
