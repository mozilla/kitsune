from typing import Any

from kitsune.llm.categorization.prompt import (
    DEFAULT_PRODUCT_RESULT,
    DEFAULT_TOPIC_RESULT,
    build_topic_prompt,
    product_parser,
    product_prompt,
    topic_parser,
)
from kitsune.llm.utils import build_chain_with_retry, get_llm
from kitsune.products.utils import get_products, get_taxonomy


def classify_product(payload: dict[str, Any], only_with_forums: bool = True) -> dict[str, Any]:
    """
    Classify content for product reassignment.

    Args:
        payload: Dict containing:
            - subject: Subject/title of the content
            - content: Main content body
            - product: Current product object
        only_with_forums: If True, only include products with forums

    Returns:
        Dict with product_result containing product, confidence, reason
    """
    llm = get_llm()

    payload["products"] = get_products(
        only_with_forums=only_with_forums,
        include_metadata=["description"],
        output_format="JSON",
    )

    product_classification_chain = build_chain_with_retry(
        product_prompt, llm, product_parser, default_result=DEFAULT_PRODUCT_RESULT
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
    product = payload["product"]

    # Ensure topics are in payload
    if "topics" not in payload:
        payload["topics"] = get_taxonomy(
            product, include_metadata=["description", "examples"], output_format="JSON"
        )

    topic_prompt = build_topic_prompt(product.title)
    topic_classification_chain = build_chain_with_retry(
        topic_prompt, llm, topic_parser, default_result=DEFAULT_TOPIC_RESULT
    )

    result = topic_classification_chain.invoke(payload)
    return {"topic_result": result}
