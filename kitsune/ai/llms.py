from functools import cache

from langchain_core.language_models.chat_models import BaseChatModel


def is_openai_model(model_name: str) -> bool:
    """
    Returns whether or not the given model name is an OpenAI model.
    """
    return any(
        model_name.startswith(prefix) for prefix in ("gpt-", "chatgpt-", "o1-", "o3-", "o4-")
    )


@cache
def get_llm(
    model_name: str, temperature: int = 0, max_tokens: int | None = None, max_retries: int = 2
) -> BaseChatModel:
    """
    Returns a LangChain chat model instance based on the given LLM model name.
    """
    if is_openai_model(model_name):
        from langchain_openai import ChatOpenAI as ChatAI
    else:
        from langchain_google_vertexai import ChatVertexAI as ChatAI

    return ChatAI(
        model=model_name, temperature=temperature, max_tokens=max_tokens, max_retries=max_retries
    )
