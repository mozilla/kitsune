from functools import cache

from kitsune.questions.prompt import get_json_result, get_prompt, get_spam_prompt


def is_openai_model(model_name):
    """
    Returns whether or not the given model name is an OpenAI model.
    """
    return any(
        model_name.startswith(prefix) for prefix in ("gpt-", "chatgpt-", "o1-", "o3-", "o4-")
    )


@cache
def get_chat_model(model_name):
    """
    Returns a LangChain chat model instance based on the given model name.
    """
    kwargs = dict(model=model_name, temperature=0, max_tokens=None, max_retries=2)

    if is_openai_model(model_name):
        from langchain_openai import ChatOpenAI as ChatAI
    else:
        from langchain_google_vertexai import ChatVertexAI as ChatAI

    return ChatAI(**kwargs)


def select_topic(model_name, question, **kwargs):
    """
    Invokes the LLM specified by the given model name to select an appropriate
    topic for the given question.
    """
    prompt = get_prompt(question, **kwargs)
    llm = get_chat_model(model_name)
    response = llm.invoke(prompt)
    return get_json_result(response.content)


def is_spam(model_name, question):
    """
    Invokes the LLM specified by the given model name to check if the given
    question is spam.
    """
    prompt = get_spam_prompt(question)
    llm = get_chat_model(model_name)
    response = llm.invoke(prompt)
    return "spam" in response.content.lower()
