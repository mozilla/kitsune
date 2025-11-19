from typing import TYPE_CHECKING, Any

from kitsune.llm.categorization.classifiers import classify_product, classify_topic
from kitsune.llm.spam.classifier import (
    ModerationAction,
    classify_spam,
    determine_action_from_spam_result,
)
from kitsune.products.models import Product
from kitsune.products.utils import get_taxonomy

if TYPE_CHECKING:
    from kitsune.customercare.models import SupportTicket
    from kitsune.questions.models import Question


def classify_question(question: "Question") -> dict[str, Any]:
    """
    Analyze a question for spam and, if not spam or low confidence, classify the topic.
    Returns a dict with keys: action, spam_result, topic_result (optional).
    """
    product = question.product
    payload: dict[str, Any] = {
        "subject": question.title,
        "content": question.content,
        "product": product,
        "topics": get_taxonomy(
            product, include_metadata=["description", "examples"], output_format="JSON"
        ),
    }

    # First classify for spam
    spam_result_dict = classify_spam(payload)
    spam_result = spam_result_dict["spam_result"]

    def handle_spam(payload: dict[str, Any], spam_result: dict[str, Any]) -> dict[str, Any]:
        """Handle spam classification with potential product reclassification."""
        action = determine_action_from_spam_result(spam_result)

        if not ((action == ModerationAction.SPAM) and spam_result.get("maybe_misclassified")):
            return {"action": action, "product_result": {}}

        # Maybe misclassified - check product reassignment
        product_result_dict = classify_product(payload, only_with_forums=True)
        product_result = product_result_dict["product_result"]
        new_product_title = product_result.get("product")

        if (
            new_product_title
            and (new_product_title != product.title)
            and (new_product := Product.active.filter(title=new_product_title).first())
        ):
            # This wasn't spam. It was a question asked under the wrong product. Reassign
            # the payload's product, clear its existing topics so they'll be regenerated
            # from the new product, and then run the topic classification.
            payload["product"] = new_product
            payload.pop("topics", None)
            topic_result_dict = classify_topic(payload)
            return {
                "action": ModerationAction.NOT_SPAM,
                "product_result": product_result,
                "topic_result": topic_result_dict["topic_result"],
            }
        else:
            return {
                "action": ModerationAction.SPAM,
                "product_result": product_result,
            }

    def decision_lambda(payload: dict[str, Any]) -> dict[str, Any]:
        is_spam: bool = spam_result.get("is_spam", False)

        base_result = {
            "spam_result": spam_result,
            "product_result": {},
            "topic_result": {},
        }

        if is_spam:
            spam_handling = handle_spam(payload, spam_result)
            return {**base_result, **spam_handling}

        # Not spam - classify topic
        topic_result_dict = classify_topic(payload)
        return {
            **base_result,
            "action": ModerationAction.NOT_SPAM,
            "topic_result": topic_result_dict["topic_result"],
        }

    return decision_lambda(payload)


def classify_zendesk_submission(submission: "SupportTicket") -> dict[str, Any]:
    """
    Analyze a support ticket for spam, product classification, and topic classification.
    Returns a dict with keys: action, spam_result, product_result, topic_result.
    """
    product = submission.product
    payload: dict[str, Any] = {
        "subject": submission.subject,
        "content": submission.description,
        "product": product,
        "topics": get_taxonomy(
            product, include_metadata=["description", "examples"], output_format="JSON"
        ),
    }

    # First classify for spam
    spam_result_dict = classify_spam(payload)
    spam_result = spam_result_dict["spam_result"]

    def handle_spam(payload: dict[str, Any], spam_result: dict[str, Any]) -> dict[str, Any]:
        """Handle spam classification with potential product reclassification."""
        action = determine_action_from_spam_result(spam_result)

        if not ((action == ModerationAction.SPAM) and spam_result.get("maybe_misclassified")):
            return {"action": action, "product_result": {}}

        # Maybe misclassified - check product reassignment
        product_result_dict = classify_product(
            payload, only_with_forums=False, current_product=product
        )
        product_result = product_result_dict["product_result"]
        new_product_title = product_result.get("product")

        if new_product_title and new_product_title != product.title:
            # If reassigned to different product, flag for review
            return {
                "action": ModerationAction.FLAG_REVIEW,
                "product_result": product_result,
                "topic_result": {},
            }
        else:
            return {
                "action": ModerationAction.SPAM,
                "product_result": product_result,
                "topic_result": {},
            }

    def decision_lambda(payload: dict[str, Any]) -> dict[str, Any]:
        is_spam: bool = spam_result.get("is_spam", False)

        base_result = {
            "spam_result": spam_result,
            "product_result": {},
            "topic_result": {},
        }

        if is_spam:
            spam_handling = handle_spam(payload, spam_result)
            return {**base_result, **spam_handling}

        # Not spam - classify topic
        topic_result_dict = classify_topic(payload)
        return {
            **base_result,
            "action": ModerationAction.NOT_SPAM,
            "topic_result": topic_result_dict["topic_result"],
        }

    return decision_lambda(payload)
