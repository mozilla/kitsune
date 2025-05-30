from typing import TYPE_CHECKING, Any

from django.db import models
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough

from kitsune.llm.questions.prompt import spam_parser, spam_prompt, topic_parser, topic_prompt
from kitsune.llm.utils import get_llm
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
        "image_urls": [image.get_absolute_url() for image in question.get_images()],
        "product": product,
        "topics": get_taxonomy(
            product, include_metadata=["description", "examples"], output_format="JSON"
        ),
    }

    spam_detection_chain = spam_prompt | llm | spam_parser
    topic_classification_chain = topic_prompt | llm | topic_parser

    def decision_lambda(payload: dict[str, Any]) -> dict[str, Any]:
        spam_result: dict[str, Any] = payload["spam_result"]
        confidence: int = spam_result.get("confidence", 0)
        is_spam: bool = spam_result.get("is_spam", False)
        result = {
            "action": ModerationAction.NOT_SPAM,
            "spam_result": spam_result,
            "topic_result": {},
        }

        if is_spam:
            match confidence:
                case _ if confidence >= HIGH_CONFIDENCE_THRESHOLD:
                    result["action"] = ModerationAction.SPAM
                case _ if (
                    confidence > LOW_CONFIDENCE_THRESHOLD
                    and confidence < HIGH_CONFIDENCE_THRESHOLD
                ):
                    result["action"] = ModerationAction.FLAG_REVIEW

        if result["action"] == ModerationAction.NOT_SPAM:
            result["topic_result"] = topic_classification_chain.invoke(payload)

        return result

    pipeline = RunnablePassthrough.assign(spam_result=spam_detection_chain) | RunnableLambda(
        decision_lambda
    )
    result: dict[str, Any] = pipeline.invoke(payload)
    return result
