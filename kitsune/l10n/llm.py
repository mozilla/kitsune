from functools import cache

from kitsune.l10n.models import MachineTranslationServiceRecord
from kitsune.l10n.prompt import get_prompt, get_result


def is_openai_model(model_name):
    """
    Returns whether or not the given model name is an OpenAI model.
    """
    return any(
        model_name.startswith(prefix)
        for prefix in (
            "gpt-",
            "chatgpt-",
            "o1-",
        )
    )


def record_localization(doc, content_attribute, target_locale, llm, prompt, response):
    """
    Records the machine translation API transaction in the database.
    """
    if content_attribute == "title":
        content_attribute = "document.title"

    service = (
        MachineTranslationServiceRecord.SERVICE_OPENAI_API
        if is_openai_model(llm.model_name)
        else MachineTranslationServiceRecord.SERVICE_VERTEX_AI_API
    )

    return MachineTranslationServiceRecord.objects.create(
        service=service,
        model_name=llm.model_name,
        target_locale=target_locale,
        source_attribute=content_attribute,
        source_revision=doc.latest_localizable_revision,
        details=dict(
            model_info=llm.model_dump(),
            input=[msg.pretty_repr() for msg in prompt],
            output=response.content,
        ),
    )


@cache
def get_chat_model(model_name):
    """
    Returns a LangChain chat model instance based on the given model name.
    """
    # The Vertex AI API has a rate limit of 60 requests-per-minute for their
    # flagship model. The OpenAI API is rate-limited per organization, which
    # in our case is 10K requests-per-minute. The average latency of Vertex
    # AI API requests seems to be about 3-4 seconds, and I expect the average
    # latency of OpenAI API requests to be more than a second, so for now we
    # can avoid using a rate limiter (also the InMemoryRateLimiter that
    # LangChain provides is not really stable yet).

    kwargs = dict(
        model=model_name,
        temperature=0,
        max_tokens=None,
        max_retries=2,
        timeout=120,
    )

    if is_openai_model(model_name):
        from langchain_openai import ChatOpenAI as ChatAI
    else:
        from langchain_google_vertexai import ChatVertexAI as ChatAI

    return ChatAI(**kwargs)


def get_localization(model_name, doc, content_attribute, target_locale):
    """
    Invokes the LLM specified by the given model name to localize the value of
    the given content attribute of the given document targeting the given locale.
    """
    prompt = get_prompt(doc, content_attribute, target_locale)
    llm = get_chat_model(model_name)
    response = llm.invoke(prompt)
    record_localization(doc, content_attribute, target_locale, llm, prompt, response)
    return get_result(response.content)
