from typing import Any

from kitsune.llm.categorization.prompt import (
    DEFAULT_PRODUCT_RESULT,
    DEFAULT_TOPIC_RESULT,
    build_product_prompt,
    build_topic_prompt,
    product_parser,
    topic_parser,
)
from kitsune.llm.utils import build_chain_with_retry, get_llm
from kitsune.products.utils import get_products, get_taxonomy


def classify_product(
    payload: dict[str, Any], only_with_forums: bool = True, current_product=None
) -> dict[str, Any]:
    """
    Classify content for product reassignment.

    Args:
        payload: Dict containing:
            - subject: Subject/title of the content
            - content: Main content body
            - product: Current product object
        only_with_forums: If True, only include products with forums
        current_product: Optional Product object. If provided, used to build
            context-specific prompt (e.g., special instructions for Mozilla Accounts).

    Returns:
        Dict with product_result containing product, confidence, reason
    """
    llm = get_llm()

    payload["products"] = get_products(
        only_with_forums=only_with_forums,
        include_metadata=["description"],
        output_format="JSON",
    )

    # Use current_product from parameter, or fall back to product in payload
    product_for_prompt = current_product or payload.get("product")

    product_prompt_template = build_product_prompt(product_for_prompt)
    product_classification_chain = build_chain_with_retry(
        product_prompt_template, llm, product_parser, default_result=DEFAULT_PRODUCT_RESULT
    )

    result = product_classification_chain.invoke(payload)
    return {"product_result": result}


def classify_topic(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Classify content into a topic.

    Args:
        payload: Dict containing:
            - subject: Subject/title of the content
            - content: Main content body
            - product: Product object
            - topics: Taxonomy JSON (if not provided, will be fetched)

    Returns:
        Dict with topic_result containing topic and reason
    """
    llm = get_llm()

    # Ensure topics are in payload
    if "topics" not in payload:
        product = payload["product"]
        payload["topics"] = get_taxonomy(
            product, include_metadata=["description", "examples"], output_format="JSON"
        )

    topic_prompt = build_topic_prompt()
    topic_classification_chain = build_chain_with_retry(
        topic_prompt, llm, topic_parser, default_result=DEFAULT_TOPIC_RESULT
    )

    result = topic_classification_chain.invoke(payload)
    return {"topic_result": result}
