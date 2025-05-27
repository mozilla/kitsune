from typing import TYPE_CHECKING, Any

from django.db import models
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough

from kitsune.llm.questions.prompt import (
    product_parser,
    product_prompt,
    spam_parser,
    spam_prompt,
    topic_parser,
    topic_prompt,
)
from kitsune.llm.utils import get_llm

# TODO:
# from kitsune.products.utils import get_products, get_taxonomy
from kitsune.products.utils import get_taxonomy

DEFAULT_LLM_MODEL = "gemini-2.5-flash-preview-04-17"
HIGH_CONFIDENCE_THRESHOLD = 75
LOW_CONFIDENCE_THRESHOLD = 60

if TYPE_CHECKING:
    from kitsune.questions.models import Question


class ModerationAction(models.TextChoices):
    NOT_SPAM = "not_spam", "Not Spam"
    SPAM = "spam", "Spam"
    FLAG_REVIEW = "flag_review", "Flag for Review"


def classify_question(question: "Question") -> dict[str, Any]:
    """
    Analyze a question for spam and, if not spam or low confidence, classify the topic.
    Returns a dict with keys: action, spam_result, topic_result (optional).
    """
    llm = get_llm(model_name=DEFAULT_LLM_MODEL)

    product = question.product
    payload: dict[str, Any] = {
        "subject": question.title,
        "question": question.content,
        "product": product,
        "topics": get_taxonomy(
            product, include_metadata=["description", "examples"], output_format="JSON"
        ),
    }

    spam_detection_chain = spam_prompt | llm | spam_parser
    product_classification_chain = product_prompt | llm | product_parser
    topic_classification_chain = topic_prompt | llm | topic_parser

    def handle_spam(payload: dict[str, Any], spam_result: dict[str, Any]) -> dict[str, Any]:
        """Handle spam classification with potential product reclassification."""
        confidence = spam_result.get("confidence", 0)
        match confidence:
            case _ if confidence >= HIGH_CONFIDENCE_THRESHOLD:
                action = ModerationAction.SPAM
            case _ if confidence > LOW_CONFIDENCE_THRESHOLD:
                action = ModerationAction.FLAG_REVIEW
            case _:
                action = ModerationAction.NOT_SPAM

        if not ((action == ModerationAction.SPAM) and spam_result.get("maybe_misclassified")):
            return {"action": action, "product_result": {}}

        # TODO:
        # payload["products"] = get_products(output_format="JSON")
        product_result = product_classification_chain.invoke(payload)
        new_product = product_result.get("product")

        if new_product and new_product != payload["product"]:
            payload["product"] = new_product
            payload["topics"] = get_taxonomy(
                new_product, include_metadata=["description", "examples"], output_format="JSON"
            )
            topic_result = topic_classification_chain.invoke(payload)
            return {
                "action": ModerationAction.NOT_SPAM,
                "product_result": product_result,
                "topic_result": topic_result,
            }
        else:
            return {
                "action": ModerationAction.SPAM,
                "product_result": product_result,
            }

    def decision_lambda(payload: dict[str, Any]) -> dict[str, Any]:
        spam_result: dict[str, Any] = payload["spam_result"]
        is_spam: bool = spam_result.get("is_spam", False)

        base_result = {
            "spam_result": spam_result,
            "product_result": {},
            "topic_result": {},
        }

        if is_spam:
            spam_handling = handle_spam(payload, spam_result)
            return {**base_result, **spam_handling}

        topic_result = topic_classification_chain.invoke(payload)
        return {**base_result, "topic_result": topic_result}

    pipeline = RunnablePassthrough.assign(spam_result=spam_detection_chain) | RunnableLambda(
        decision_lambda
    )
    result: dict[str, Any] = pipeline.invoke(payload)
    return result
