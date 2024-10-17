from django.conf import settings
from django.template.loader import render_to_string
from langchain_core.messages import HumanMessage, SystemMessage


BEGIN_RESULT = "<<<begin-result>>>"
END_RESULT = "<<<end-result>>>"


def get_language_in_english(locale):
    """
    Returns the name of the locale in English, for example "it" returns "Italian"
    and "pt-BR" returns "Portuguese (Brazilian)".
    """
    return settings.LOCALES[locale].english


def get_example(doc, content_attribute, target_locale):
    """
    Returns a dictionary containing the most recent translation of the given
    revision's document, or None if no approved translation exists.
    """
    trans_doc = doc.translated_to(target_locale)

    if not (
        trans_doc
        and (example_target := trans_doc.current_revision)
        and (example_source := example_target.based_on)
    ):
        return None

    return dict(
        source_text=getattr(example_source, content_attribute),
        target_text=getattr(example_target, content_attribute),
    )


def get_messages(
    source_text, source_locale, target_locale, example=None, include_wiki_instructions=False
):
    """
    A generic function for returning a list of LLM messages ("syste," and "user"
    messages)
    """
    context = dict(
        example=example,
        source_text=source_text,
        source_language=get_language_in_english(source_locale),
        target_language=get_language_in_english(target_locale),
        include_wiki_instructions=include_wiki_instructions,
        result_delimiter_begin=BEGIN_RESULT,
        result_delimiter_end=END_RESULT,
    )
    return [
        SystemMessage(content=render_to_string("l10n/llm_system_message.txt", context)),
        HumanMessage(content=render_to_string("l10n/llm_user_message.txt", context)),
    ]


def get_prompt(doc, content_attribute, target_locale):
    """
    Returns a list of LLM messages (a "system" message plus a "user" message) for
    use as the prompt when invoking a response from an LLM model. The messages
    comprise a request to translate the given document's specific content defined
    by the given "content_attribute" into the language of the given target locale.
    """
    if content_attribute == "title":
        example = None
        source_text = doc.title
    else:
        example = get_example(doc, content_attribute, target_locale)
        source_text = getattr(doc.latest_localizable_revision, content_attribute)

    return get_messages(
        source_text=source_text,
        source_locale=doc.locale,
        target_locale=target_locale,
        example=example,
        include_wiki_instructions=content_attribute in ("summary", "content"),
    )


def get_result(text):
    """
    Given the text of the LLM response, extracts and returns the actual translation.
    """
    return text.split(BEGIN_RESULT)[-1].split(END_RESULT)[0]
