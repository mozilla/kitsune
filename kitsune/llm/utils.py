from functools import lru_cache, reduce
from typing import Any, cast

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from langchain.chat_models.base import BaseChatModel
from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.runnables.base import RunnableLike, coerce_to_runnable
from langchain_google_vertexai import ChatVertexAI
from openai import APIError, OpenAI
from openai.types.decision_create_params import Question as DecisionQuestion

DEFAULT_LLM_MODEL = "gemini-2.5-flash"


@lru_cache(maxsize=1)
def get_llm(
    model_name: str = DEFAULT_LLM_MODEL,
    temperature: float = 0.3,
    max_tokens: int | None = None,
    max_retries: int = 2,
) -> BaseChatModel:
    """
    Returns a LangChain chat model instance based on the given LLM model name.
    """
    return ChatVertexAI(
        model=model_name, temperature=temperature, max_tokens=max_tokens, max_retries=max_retries
    )


def parse_probability(value: Any) -> float | None:
    """Accept finite probabilities, not booleans or numeric strings."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        return None
    return float(value)


def get_probability_setting(name: str) -> float:
    value = parse_probability(getattr(settings, name))
    if value is None:
        raise ImproperlyConfigured(f"{name} must be a finite probability between 0 and 1.")
    return value


class DecisionError(RuntimeError):
    """The Decisions service could not evaluate a classification request."""


@lru_cache(maxsize=1)
def get_decisions_client(api_key: str, base_url: str, timeout: float) -> OpenAI:
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=2)


def evaluate_decisions(
    input_text: str, questions: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Evaluate named questions through the centrally configured Decisions client."""
    if not settings.OPENAI_API_KEY:
        raise DecisionError("OpenAI Decisions credentials are not configured.")

    try:
        decision = get_decisions_client(
            settings.OPENAI_API_KEY,
            settings.OPENAI_BASE_URL,
            settings.DECISIONS_TIMEOUT_SECONDS,
        ).decisions.create(
            model=settings.DECISIONS_MODEL,
            input=input_text,
            questions=cast(list[DecisionQuestion], questions),
        )
    except APIError as exc:
        raise DecisionError(f"Decisions request failed ({type(exc).__name__}).") from exc

    return {
        answer.name: answer.model_dump() for answer in decision.answers if answer.name is not None
    }


def build_chain_with_retry(
    *stages: RunnableLike, default_result: Any = None, max_retries: int = 1
) -> Runnable:
    """
    Build a chain that can retry on OutputParserException exceptions.
    """

    # The "coerce_to_runnable" is only needed here just in case the first stage is
    # not a Runnable, because all subsequent stages will be coerced to a Runnable
    # within the Runnable.__or__ method when chained via the "or" operator ("|").
    chain = reduce(
        lambda x, y: x | y,
        (coerce_to_runnable(stage) if i == 0 else stage for i, stage in enumerate(stages)),
    )

    def chain_with_retry(payload: Any, retry: int = 0) -> Any:
        """Chain with retry for OutputParserException exceptions."""
        try:
            return chain.invoke(payload)
        except OutputParserException:
            if retry < max_retries:
                return chain_with_retry(payload, retry=retry + 1)
            return default_result

    return RunnableLambda(chain_with_retry)
