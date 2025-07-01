from functools import lru_cache

from langchain.chat_models.base import BaseChatModel

DEFAULT_LLM_MODEL = "gemini-2.5-flash-preview-04-17"


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
        model=model_name, temperature=temperature, max_tokens=max_tokens, max_retries=max_retries
    )
