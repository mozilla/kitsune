import json

import yaml
from django.db.models import Prefetch, Q

from kitsune.products.models import Product, Topic


def get_taxonomy(
    product: Product | str | None = None,
    include_metadata: list[str] | tuple[str, ...] | None = None,
    output_format: str = "YAML",
) -> str:
    """
    Returns the currently active taxonomy as a string in the output format requested
    (either "YAML" or "JSON"). If a product is given, the taxonomy is limited to that
    product, otherwise the entire taxonomy, spanning all products, is returned. Requires
    only a single database query if a specific product is given, otherwise two queries.
    """

    result = {}

    qs_topics = Topic.active.filter(visible=True).select_related("parent")

    if product:
        if isinstance(product, Product):
            qs_topics = qs_topics.filter(products=product)
        else:
            qs_topics = qs_topics.filter(
                products__in=Product.active.filter(Q(title=product) | Q(slug=product))
            )
    else:
        qs_products = Product.active.filter(Q(visible=True) | Q(slug="mozilla-account"))
        qs_topics = (
            qs_topics.filter(products__in=qs_products)
            .distinct()
            .prefetch_related(
                Prefetch("products", qs_products.only("id", "title").order_by("title"))
            )
        )

    # Get all of the topics and organize them by parent.
    topics_by_parent: dict[None | int, list[Topic]] = dict()
    for topic in qs_topics.only(
        "id", "title", "parent", "metadata" if include_metadata else "description"
    ).order_by("title"):
        topics_by_parent.setdefault(topic.parent.id if topic.parent else None, []).append(topic)

    def get_topics(parent=None):
        """
        Recursive function that returns the topics with the given parent.
        """
        result = []

        for topic in topics_by_parent.get(parent.id if parent else None, ()):
            item = dict(title=topic.title)

            if include_metadata:
                if not topic.metadata:
                    # Skip topics that don't have any metadata.
                    continue
                for name in include_metadata:
                    if value := topic.metadata.get(name):
                        item[name] = value
            else:
                item["description"] = topic.description

            if not product:
                item["products"] = [{"title": p.title} for p in topic.products.all()]
            item["subtopics"] = get_topics(parent=topic)

            result.append(item)

        return result

    result["topics"] = get_topics()

    if output_format.lower() == "json":
        return json.dumps(result, indent=2, sort_keys=False)

    return yaml.dump(result, indent=2, sort_keys=False)


def get_products(output_format: str = "YAML") -> str:
    """
    Returns the currently active products, each with their title and description,
    as a string in the output format requested (either "YAML" or "JSON").
    """
    products: list[dict[str, str]] = []
    result = dict(products=products)

    for product in Product.active.filter(Q(visible=True) | Q(slug="mozilla-account")):
        products.append(
            dict(
                title=product.title,
                description=product.description,
            )
        )

    if output_format.lower() == "json":
        return json.dumps(result, indent=2, sort_keys=False)

    return yaml.dump(result, indent=2, sort_keys=False)
