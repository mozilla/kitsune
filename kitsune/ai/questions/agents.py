from functools import cache

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from kitsune.ai.llms import get_llm
from kitsune.ai.questions.prompts import get_system_prompt
from kitsune.ai.questions.tools import assign_topic, flag_as_spam
from kitsune.ai.utils import has_tool_been_called
from kitsune.products.models import Product
from kitsune.questions.models import Question


@cache
def get_agents(product: Product, model_name: str = "gemini-2.5-flash-preview-04-17"):
    """
    Creates and returns the spam and topic agents for the given product and LLM model.
    """
    model = get_llm(model_name)
    spam_agent = create_react_agent(
        model=model,
        prompt=get_system_prompt("spam", product),
        tools=[flag_as_spam],
        name="spam_agent",
    )
    topic_agent = create_react_agent(
        model=model,
        prompt=get_system_prompt("topic", product),
        tools=[assign_topic],
        name="topic_agent",
    )
    return spam_agent, topic_agent


def classify(question: Question, model_name: str = "gemini-2.5-flash-preview-04-17") -> None:
    """
    Top-level agent that manages spam and topic agents in order to first determine whether
    or not to classify a question as spam, and if not, then assign a topic to the question.
    """
    spam_agent, topic_agent = get_agents(question.product, model_name)

    input = dict(
        messages=[
            HumanMessage(f"Question ID = {question.id}\nQuestion:\n{question.content}"),
        ]
    )

    spam_response = spam_agent.invoke(input)

    if not has_tool_been_called("flag_as_spam", spam_response):
        topic_agent.invoke(input)
