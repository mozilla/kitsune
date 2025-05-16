from functools import cache

from langchain_google_vertexai import ChatVertexAI


@cache
def get_llm(
    model_name: str,
    temperature: int = 1,
    max_tokens: int | None = None,
    max_retries: int = 2,
) -> ChatVertexAI:
    """
    Returns a LangChain chat model instance based on the given LLM model name.
    """
    return ChatVertexAI(
        model=model_name, temperature=temperature, max_tokens=max_tokens, max_retries=max_retries
    )
