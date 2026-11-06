from functools import lru_cache, reduce
from typing import Any

from langchain.chat_models.base import BaseChatModel
from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.runnables.base import RunnableLike, coerce_to_runnable

DEFAULT_LLM_MODEL = "gemini-3.8-flash"


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
    from langchain_google_vertexai import ChatVertexAI

    return ChatVertexAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
        # Newer Gemini models (e.g. gemini-4-argon) aren't served from regional endpoints.
        location="global",
    )


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
