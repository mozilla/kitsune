from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.utils.translation import gettext as _

from kitsune.flagit.models import FlaggedObject
from kitsune.llm.categorization.classifiers import classify_product, classify_topic
from kitsune.llm.spam.classifier import (
    ModerationAction,
    classify_spam,
    determine_action_from_spam_result,
)
from kitsune.products.models import Product, ProductSupportConfig, Topic, ZendeskTopic

if TYPE_CHECKING:
    from kitsune.customercare.models import SupportTicket
    from kitsune.questions.models import Question


def _classify_support(payload: dict[str, Any], *, skip_spam: bool = False) -> dict[str, Any]:
    """Screen spam before resolving the product and its topic."""
    original_product = payload["product"]
    result: dict[str, Any] = {
        "action": ModerationAction.NOT_SPAM,
        "submitted_product_id": original_product.pk if original_product else None,
        "spam_result": {},
        "product_result": {},
        "topic_result": {},
        "assessment_payload": None,
    }

    if not skip_spam:
        result.update(classify_spam(payload))
        spam_result = result["spam_result"]
        action = determine_action_from_spam_result(spam_result)
        result["action"] = action
        if action != ModerationAction.NOT_SPAM:
            if action == ModerationAction.FLAG_REVIEW and None not in (
                spam_result.get("probability"),
                spam_result.get("relevance_uncertainty_probability"),
            ):
                result["assessment_payload"] = {
                    key: payload[key] for key in ("subject", "content", "channel", "locale")
                }
            return result

    result.update(classify_product(payload))
    resolved_product_id = result["product_result"]["product_id"]
    if resolved_product_id is None:
        result["action"] = ModerationAction.FLAG_REVIEW
        result["review_reason"] = FlaggedObject.REASON_CONTENT_MODERATION
        return result
    if resolved_product_id != result["submitted_product_id"]:
        payload["product"] = Product.active.get(pk=resolved_product_id)
        payload.pop("selected_topic", None)
    result.update(classify_topic(payload))
    return result


def question_payload(question: Question) -> dict[str, str]:
    """Build the shared, product-neutral content input for a public question."""
    return {
        "subject": question.title,
        "content": question.content,
        "channel": "forum",
        "locale": question.locale,
    }


def ticket_payload(submission: SupportTicket) -> dict[str, str]:
    """Build the shared content input for a private support ticket."""
    return {
        "subject": submission.subject,
        "content": submission.description,
        "channel": "ticket",
        "locale": settings.LANGUAGE_CODE,
    }


def classify_question(question: Question) -> dict[str, Any]:
    """Classify an admitted question's product and then its resolved-product topic."""
    payload: dict[str, Any] = question_payload(question)
    payload.update(product=question.product, user=question.creator)
    if question.topic_id:
        payload["selected_topic"] = question.topic.title
    return _classify_support(payload)


def classify_zendesk_submission(submission: SupportTicket) -> dict[str, Any]:
    """Keep private submissions in ticket-capable destinations after spam screening."""
    payload: dict[str, Any] = ticket_payload(submission)
    payload.update(product=submission.product, user=submission.user)
    if submission.category:
        selected = (
            ZendeskTopic.objects.filter(slug=submission.category).select_related("topic").first()
        )
        if selected and selected.topic_id:
            payload["selected_topic"] = selected.topic.title

    try:
        config = submission.product.support_configs.select_related("zendesk_config").get(
            is_active=True
        )
    except ProductSupportConfig.DoesNotExist:
        skip_spam = False
    else:
        skip_spam = bool(config.zendesk_config and config.zendesk_config.skip_spam_moderation)
    return _classify_support(payload, skip_spam=skip_spam)


def classification_notes(result: dict[str, Any]) -> str:
    """Describe recorded decisions without inventing an explanation for the model."""
    spam = result.get("spam_result", {})
    product = result.get("product_result", {})
    topic = result.get("topic_result", {})
    lines = [
        _("Classification model: {model}").format(model=settings.DECISIONS_MODEL),
        _("Action: {action}").format(action=result.get("action")),
    ]
    if spam:
        lines.extend(
            [
                _("Spam probability: {probability}").format(probability=spam.get("probability")),
                _("Relevance-only uncertainty probability: {probability}").format(
                    probability=spam.get("relevance_uncertainty_probability")
                ),
                _("Spam cutoffs: review {review}, reject {reject}").format(
                    review=settings.SPAM_REVIEW_PROBABILITY,
                    reject=settings.SPAM_REJECT_PROBABILITY,
                ),
            ]
        )
        if spam.get("reason"):
            lines.append(spam["reason"])

    product_ids = {
        result.get("submitted_product_id"),
        product.get("predicted_product_id"),
        product.get("product_id"),
    } - {None}
    products = dict(Product.objects.filter(pk__in=product_ids).values_list("pk", "title"))
    for label, product_id in (
        (_("Submitted product"), result.get("submitted_product_id")),
        (_("Predicted product"), product.get("predicted_product_id")),
        (_("Resolved product"), product.get("product_id")),
    ):
        if product_id is not None:
            lines.append(f"{label}: {products.get(product_id, product_id)}")
    if product:
        lines.append(
            _("Product probability: {probability}").format(probability=product.get("probability"))
        )
        if product.get("reason"):
            lines.append(product["reason"])
    if topic:
        topic_title = None
        if (topic_id := topic.get("topic_id")) is not None:
            topic_title = Topic.objects.filter(pk=topic_id).values_list("title", flat=True).first()
        lines.append(_("Topic: {topic}").format(topic=topic_title or _("Undefined")))
        lines.append(
            _("Topic probability: {probability}").format(probability=topic.get("probability"))
        )
        if topic.get("reason"):
            lines.append(topic["reason"])
    if result.get("assessment_payload"):
        lines.append(_("Advisory spam assessment requested."))
    return "\n".join(lines)
