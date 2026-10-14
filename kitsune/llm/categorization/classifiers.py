import json
from types import SimpleNamespace
from typing import Any

from django.conf import settings
from django.db.models import Q, prefetch_related_objects
from django.utils.translation import gettext as _

from kitsune.llm.categorization.prompt import PRODUCT_INSTRUCTIONS, TOPIC_INSTRUCTIONS
from kitsune.llm.utils import (
    DecisionError,
    evaluate_decisions,
    get_probability_setting,
    parse_probability,
)
from kitsune.products.models import Product, ProductSupportConfig
from kitsune.products.utils import get_taxonomy


def _selected_choice(answer: Any, choices: dict[str, Any]) -> tuple[str, float] | None:
    """Read a supplied option's probability, never the separate answer confidence."""
    match answer:
        case {
            "type": "choice",
            "choice": str() as selected,
            "probabilities": list() as probabilities,
        } if selected in choices:
            pass
        case _:
            return None

    distribution = {}
    for entry in probabilities:
        if not isinstance(entry, dict):
            return None
        value = entry.get("value")
        probability = parse_probability(entry.get("probability"))
        if (
            not isinstance(value, str)
            or value not in choices
            or value in distribution
            or probability is None
        ):
            return None
        distribution[value] = probability
    if selected not in distribution:
        return None
    return selected, distribution[selected]


def eligible_products(payload: dict[str, Any], *, product_id: int | None = None) -> list[Product]:
    """Apply the shared routing policy, optionally restricted to one destination."""
    user = payload["user"]
    if user is None:
        return []
    match payload.get("channel"):
        case "forum":
            locale = payload.get("locale")
            if not isinstance(locale, str) or not locale:
                return []
            products = Product.active.with_question_forums(locale)
            support_type = ProductSupportConfig.SUPPORT_TYPE_FORUM
        case "ticket":
            products = Product.active.filter(
                support_configs__is_active=True,
                support_configs__zendesk_config__isnull=False,
            ).distinct()
            support_type = ProductSupportConfig.SUPPORT_TYPE_ZENDESK
        case _:
            return []

    products = products.filter(Q(visible=True) | Q(slug="mozilla-account"))
    if product_id is not None:
        products = products.filter(pk=product_id)
    request = SimpleNamespace(user=user, GET={"support_type": support_type})
    return [
        product
        for product in products.order_by("pk")
        if ProductSupportConfig.objects.route_support_request(request, product)[0] == support_type
    ]


def eligible_product(payload: dict[str, Any], product_id: int | None) -> Product | None:
    """Revalidate one destination without rebuilding the routing catalog."""
    if product_id is None:
        return None
    return next(iter(eligible_products(payload, product_id=product_id)), None)


def classify_product(payload: dict[str, Any]) -> dict[str, Any]:
    """Choose an eligible product, retaining the selection unless reassignment is decisive."""
    current_product = payload.get("product")
    threshold = get_probability_setting("PRODUCT_REASSIGN_PROBABILITY")
    account_threshold = get_probability_setting("MOZILLA_ACCOUNT_REASSIGN_PROBABILITY")
    if current_product and current_product.slug == "mozilla-account":
        threshold = max(threshold, account_threshold)
    result = {
        "product_id": current_product.pk if current_product else None,
        "predicted_product_id": None,
        "probability": None,
        "reassigned": False,
        "reason": "",
    }
    response = {"product_result": result}
    channel = payload.get("channel")
    match channel:
        case "forum" if not isinstance(payload.get("locale"), str) or not payload["locale"]:
            result["reason"] = _("Product selection abstained: forum locale is missing.")
            return response
        case "forum" | "ticket":
            pass
        case _:
            result["reason"] = _("Product selection abstained: submission channel is unsupported.")
            return response

    products = eligible_products(payload)
    if not products:
        result["reason"] = _("Product selection abstained: no eligible destinations.")
        return response
    if len(products) + 1 > settings.DECISIONS_MAX_CHOICES:
        result["reason"] = _(
            "Product selection abstained: catalog including Unknown exceeds the "
            "{limit}-choice limit."
        ).format(limit=settings.DECISIONS_MAX_CHOICES)
        return response

    prefetch_related_objects(products, "platforms")
    product_choices: dict[str, Product | None] = {
        f"product:{product.pk}": product for product in products
    }

    choices = [
        {
            "value": value,
            "description": json.dumps(
                {
                    "title": product.title,
                    "slug": product.slug,
                    "description": (
                        product.metadata.get("description")
                        if isinstance(product.metadata, dict)
                        else None
                    )
                    or product.description,
                    "platforms": [platform.name for platform in product.platforms.all()],
                },
                ensure_ascii=False,
            ),
        }
        for value, product in product_choices.items()
        if product is not None
    ]
    choices.append(
        {
            "value": "unknown",
            "description": "Unknown, ambiguous, no eligible product, or no clear primary product.",
        }
    )
    product_choices["unknown"] = None
    input_text = json.dumps(
        {
            "subject": payload.get("subject", ""),
            "content": payload.get("content", ""),
            "channel": channel,
            "locale": payload.get("locale"),
            "selected_product": (
                {"title": current_product.title, "slug": current_product.slug}
                if current_product
                else None
            ),
        },
        ensure_ascii=False,
    )
    try:
        answers = evaluate_decisions(
            input_text,
            [
                {
                    "type": "choice",
                    "name": "product",
                    "instructions": PRODUCT_INSTRUCTIONS,
                    "choices": choices,
                }
            ],
        )
    except DecisionError:
        result["reason"] = _("Product selection abstained: classification service is unavailable.")
        return response

    selected = _selected_choice(answers.get("product"), product_choices)
    if selected is None:
        result["reason"] = _(
            "Product selection abstained: answer is missing, refused, or invalid."
        )
        return response
    value, probability = selected
    predicted = product_choices[value]
    result["probability"] = probability
    if predicted is None:
        result["reason"] = _("No unambiguous eligible primary product was selected.")
        return response

    result["predicted_product_id"] = predicted.pk
    if current_product and predicted.pk == current_product.pk:
        result["reason"] = _("The selected primary product matches the current product.")
        return response

    if probability < threshold:
        result["reason"] = _(
            "Current product retained: selected option probability {probability} "
            "is below the reassignment threshold {threshold}."
        ).format(probability=probability, threshold=threshold)
        return response

    result.update(
        product_id=predicted.pk,
        reassigned=True,
        reason=_(
            "Selected eligible product {product_id}: option probability {probability} "
            "meets the reassignment threshold {threshold}."
        ).format(product_id=predicted.pk, probability=probability, threshold=threshold),
    )
    return response


def classify_topic(payload: dict[str, Any]) -> dict[str, Any]:
    """Choose a taxonomy ID scoped to the resolved product, or explicitly abstain."""
    result: dict[str, Any] = {"topic_id": None, "probability": None, "reason": ""}
    response = {"topic_result": result}
    product = payload["product"]
    taxonomy = json.loads(
        get_taxonomy(
            product,
            include_metadata=["description", "examples"],
            output_format="JSON",
            include_ids=True,
        )
    )
    topic_choices = {}
    choices = []

    def add_topics(topics, ancestors=()):
        for topic in topics:
            value = f"topic:{topic['id']}"
            path = (*ancestors, topic["title"])
            topic_choices[value] = topic["id"]
            choices.append(
                {
                    "value": value,
                    "description": json.dumps(
                        {
                            "title": topic["title"],
                            "path": path,
                            "description": topic.get("description", ""),
                            "examples": topic.get("examples", []),
                        },
                        ensure_ascii=False,
                    ),
                }
            )
            add_topics(topic["subtopics"], path)

    add_topics(taxonomy["topics"])
    if not choices:
        result["reason"] = _("Topic selection abstained: no eligible taxonomy topics.")
        return response
    if len(choices) + 1 > settings.DECISIONS_MAX_CHOICES:
        result["reason"] = _(
            "Topic selection abstained: taxonomy including Undefined exceeds the "
            "{limit}-choice limit."
        ).format(limit=settings.DECISIONS_MAX_CHOICES)
        return response

    topic_choices["undefined"] = None
    choices.append(
        {
            "value": "undefined",
            "description": "Undefined: insufficient information or no suitable topic.",
        }
    )
    input_text = json.dumps(
        {
            "subject": payload.get("subject", ""),
            "content": payload.get("content", ""),
            "channel": payload.get("channel"),
            "locale": payload.get("locale"),
            "product": {"title": product.title, "slug": product.slug},
            "selected_topic": payload.get("selected_topic") or None,
        },
        ensure_ascii=False,
    )
    try:
        answers = evaluate_decisions(
            input_text,
            [
                {
                    "type": "choice",
                    "name": "topic",
                    "instructions": TOPIC_INSTRUCTIONS,
                    "choices": choices,
                }
            ],
        )
    except DecisionError:
        result["reason"] = _("Topic selection abstained: classification service is unavailable.")
        return response

    selected = _selected_choice(answers.get("topic"), topic_choices)
    if selected is None:
        result["reason"] = _("Topic selection abstained: answer is missing, refused, or invalid.")
        return response
    value, probability = selected
    topic_id = topic_choices[value]
    result.update(
        topic_id=topic_id,
        probability=probability,
        reason=(
            _("Undefined was selected; no taxonomy topic ID was assigned.")
            if topic_id is None
            else _(
                "Selected topic {topic_id} from the resolved product's eligible taxonomy."
            ).format(topic_id=topic_id)
        ),
    )
    return response
