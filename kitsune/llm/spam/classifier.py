from typing import Any

from django.db import models

from kitsune.llm.spam.prompt import DEFAULT_SPAM_RESULT, build_spam_prompt, spam_parser
from kitsune.llm.utils import build_chain_with_retry, get_llm

HIGH_CONFIDENCE_THRESHOLD = 75
LOW_CONFIDENCE_THRESHOLD = 60


class ModerationAction(models.TextChoices):
    NOT_SPAM = "not_spam", "Not Spam"
    SPAM = "spam", "Spam"
    FLAG_REVIEW = "flag_review", "Flag for Review"


def determine_action_from_spam_result(spam_result: dict):
    """
    Determine moderation action based on spam classification confidence.

    Args:
        spam_result: Dict with 'confidence' key

    Returns:
        ModerationAction value (SPAM, FLAG_REVIEW, or NOT_SPAM)
    """
    confidence = spam_result.get("confidence", 0)
    match confidence:
        case _ if confidence >= HIGH_CONFIDENCE_THRESHOLD:
            return ModerationAction.SPAM
        case _ if confidence > LOW_CONFIDENCE_THRESHOLD:
            return ModerationAction.FLAG_REVIEW
        case _:
            return ModerationAction.NOT_SPAM


def classify_spam(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Classify content for spam detection.

    Args:
        payload: Dict containing:
            - subject: Subject/title of the content
            - content: Main content body (question/ticket description)
            - product: Product object (used to determine prompt type)

    Returns:
        Dict with spam_result containing is_spam, confidence, reason, maybe_misclassified
    """
    llm = get_llm()
    product = payload["product"]

    spam_prompt = build_spam_prompt(product)
    spam_detection_chain = build_chain_with_retry(
        spam_prompt, llm, spam_parser, default_result=DEFAULT_SPAM_RESULT
    )

    result = spam_detection_chain.invoke(payload)
    return {"spam_result": result}
