from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from kitsune.llm.categorization.classifiers import classify_product, classify_topic
from kitsune.llm.spam.classifier import (
    ModerationAction,
    classify_spam,
    determine_action_from_spam_result,
)
from kitsune.products.models import Product, ProductSupportConfig
from kitsune.products.utils import get_taxonomy

if TYPE_CHECKING:
    from kitsune.customercare.models import SupportTicket
    from kitsune.questions.models import Question


def _handle_product_reassignment(
    payload: dict[str, Any],
    product: Product,
    only_with_forums: bool,
    on_reassignment: Callable[[dict[str, Any], Product], dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Check for product reassignment and handle accordingly.

    Args:
        payload: Classification payload
        product: Original product
        only_with_forums: Whether to only consider products with forums
        on_reassignment: Callback to handle reassignment, receives (product_result, new_product)
            and returns a dict with action, product_result, and topic_result keys.

    Returns:
        Dict with classification results if reassignment detected, None otherwise.
    """
    product_result_dict = classify_product(
        payload, only_with_forums=only_with_forums, current_product=product
    )
    product_result = product_result_dict["product_result"]
    new_product_title = product_result.get("product")

    if (
        new_product_title
        and new_product_title != product.title
        and (new_product := Product.active.filter(title=new_product_title).first())
    ):
        return on_reassignment(product_result, new_product)
    return None


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

    spam_result_dict = classify_spam(payload)
    spam_result = spam_result_dict["spam_result"]
    is_spam: bool = spam_result.get("is_spam", False)

    base_result = {
        "spam_result": spam_result,
        "product_result": {},
        "topic_result": {},
    }

    # If spam with maybe_misclassified flag, check for product reassignment
    if is_spam:
        action = determine_action_from_spam_result(spam_result)

        if (action == ModerationAction.SPAM) and spam_result.get("maybe_misclassified"):

            def on_reassignment(product_result: dict[str, Any], new_product: Product):
                # Reassign payload product and run topic classification
                payload["product"] = new_product
                payload.pop("topics", None)
                topic_result_dict = classify_topic(payload)
                return {
                    "action": ModerationAction.NOT_SPAM,
                    "product_result": product_result,
                    "topic_result": topic_result_dict["topic_result"],
                }

            result = _handle_product_reassignment(payload, product, True, on_reassignment)
            if result:
                return {**base_result, **result}
            # No reassignment - it's spam
            return {**base_result, "action": ModerationAction.SPAM, "product_result": {}}
        # Other spam action (FLAG_REVIEW or already handled)
        return {**base_result, "action": action, "product_result": {}}
    # Not spam - classify topic
    topic_result_dict = classify_topic(payload)
    return {
        **base_result,
        "action": ModerationAction.NOT_SPAM,
        "topic_result": topic_result_dict["topic_result"],
    }


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

    # Check if spam moderation should be skipped for this product
    skip_spam = False
    try:
        config = product.support_configs.get(is_active=True)
        if config.zendesk_config and config.zendesk_config.skip_spam_moderation:
            skip_spam = True
    except ProductSupportConfig.DoesNotExist:
        # If we can't determine config, fall back to normal spam checking
        pass

    base_result: dict[str, Any] = {
        "spam_result": {},
        "product_result": {},
        "topic_result": {},
    }

    def zendesk_on_reassignment(product_result: dict[str, Any], new_product: Product):
        """Handle product reassignment for Zendesk tickets."""
        if product.has_ticketing_support:
            # Original product has ticketing support - send to Zendesk with "other" tag, skip topic classification
            return {
                "action": ModerationAction.NOT_SPAM,
                "product_result": product_result,
                "topic_result": {},
            }
        # Original product doesn't have ticketing support - flag for review
        return {
            "action": ModerationAction.FLAG_REVIEW,
            "product_result": product_result,
            "topic_result": {},
        }

    # Skip spam moderation if configured
    if skip_spam:
        # Check for product reassignment
        if result := _handle_product_reassignment(
            payload, product, False, zendesk_on_reassignment
        ):
            return {**base_result, **result}

        # No reassignment - classify topic normally
        topic_result_dict = classify_topic(payload)
        return {
            **base_result,
            "action": ModerationAction.NOT_SPAM,
            "topic_result": topic_result_dict["topic_result"],
        }

    # Normal spam checking flow
    spam_result_dict = classify_spam(payload)
    spam_result = spam_result_dict["spam_result"]
    is_spam: bool = spam_result.get("is_spam", False)

    base_result["spam_result"] = spam_result

    # If spam with maybe_misclassified flag, check for product reassignment
    if is_spam:
        action = determine_action_from_spam_result(spam_result)

        if (action == ModerationAction.SPAM) and spam_result.get("maybe_misclassified"):
            result = _handle_product_reassignment(payload, product, False, zendesk_on_reassignment)
            if result:
                return {**base_result, **result}
            # No reassignment - it's spam
            return {**base_result, "action": ModerationAction.SPAM, "product_result": {}}

        # Other spam action (FLAG_REVIEW or already handled)
        return {**base_result, "action": action, "product_result": {}}

    if result := _handle_product_reassignment(payload, product, False, zendesk_on_reassignment):
        return {**base_result, **result}

    # No reassignment - classify topic normally
    topic_result_dict = classify_topic(payload)
    return {
        **base_result,
        "action": ModerationAction.NOT_SPAM,
        "topic_result": topic_result_dict["topic_result"],
    }
