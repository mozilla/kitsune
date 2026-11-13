import json

import yaml
from django.conf import settings
from django.db.models import Count, Prefetch, Q

from kitsune.groups.models import GroupProfile
from kitsune.products.models import Product, SupportCoverage, Topic


def get_enterprise_companies(request) -> list[GroupProfile]:
    """Return up to two of the active requesting user's enterprise companies.

    More than one means the company is ambiguous. They are resolved once per request.
    """
    user = request.user
    if not (user and user.is_authenticated and user.is_active):
        return []
    return GroupProfile.objects.cached_enterprise_companies(user)[:2]


def get_support_company(request) -> GroupProfile | None:
    """Return the requesting user's single enterprise company, or None for none or several."""
    companies = get_enterprise_companies(request)
    return companies[0] if len(companies) == 1 else None


def get_covered_products(company: GroupProfile) -> list[Product]:
    """Return the active products the company has effective enterprise coverage for."""
    # Overlapping coverages of one product are ambiguous, and the router denies them.
    return list(
        Product.active.filter(support_coverages__in=SupportCoverage.objects.effective(company))
        .annotate(coverage_count=Count("support_coverages"))
        .filter(coverage_count=1)
    )


def get_support_locale(company: GroupProfile, locale: str = "") -> str:
    """Return the locale if the company's contracts in effect allow it, else their default.

    English is always allowed. The default is the one extra language the contracts list, or
    English when they list none or several. Without a contract in effect, the locale is kept,
    and an empty locale becomes English.
    """
    if locale == settings.WIKI_DEFAULT_LANGUAGE:
        return locale
    language_lists = list(
        SupportCoverage.objects.effective(company).values_list("contract__languages", flat=True)
    )
    if not language_lists:
        return locale or settings.WIKI_DEFAULT_LANGUAGE
    languages = {language for contract in language_lists for language in contract}
    if locale in languages:
        return locale
    if len(languages) == 1:
        return languages.pop()
    return settings.WIKI_DEFAULT_LANGUAGE


def get_professional_support_products(request) -> list[Product]:
    """Return the active products the requesting user has effective enterprise coverage for."""
    company = get_support_company(request)
    return get_covered_products(company) if company else []


def get_professional_support(request) -> tuple[GroupProfile | None, list[Product]]:
    """Return the requesting user's company and covered products; no company without products."""
    products = get_professional_support_products(request)
    return (get_support_company(request) if products else None), products


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
    topics_by_parent: dict[int | None, list[Topic]] = {}
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
            item = {"title": topic.title}

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


def get_products(
    only_with_forums: bool = False,
    include_metadata: list[str] | tuple[str, ...] | None = None,
    output_format: str = "YAML",
) -> str:
    """
    Returns the currently active products, each with their title and description,
    as a string in the output format requested (either "YAML" or "JSON").
    """
    products: list[dict[str, str]] = []
    result = {"products": products}
    products_qs = Product.active

    if only_with_forums:
        products_qs = products_qs.with_question_forums()
    products_qs = products_qs.filter(Q(visible=True) | Q(slug="mozilla-account"))

    for product in products_qs:
        item = {"title": product.title}

        if include_metadata:
            for name in include_metadata:
                if value := product.metadata.get(name):
                    item[name] = value
        else:
            item["description"] = product.description

        products.append(item)

    if output_format.lower() == "json":
        return json.dumps(result, indent=2, sort_keys=False)

    return yaml.dump(result, indent=2, sort_keys=False)
