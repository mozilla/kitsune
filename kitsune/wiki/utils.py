import random
import time
from itertools import chain, islice

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.backends.base import SessionBase
from django.db.models import OuterRef, Q, Subquery
from django.db.models.functions import Now
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404

from kitsune.dashboards import LAST_7_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.products.models import Product, Topic
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.wiki.facets import documents_for
from kitsune.wiki.models import Document, Revision

KB_VISITED_DEFAULT_TTL = 60 * 60 * 24  # 24 hours


def active_contributors(from_date, to_date=None, locale=None, product=None):
    """Return active KB contributors for the specified parameters.

    An active KB contributor is a user that has created or reviewed a
    Revision in the given time period.

    :arg from_date: start date for contributions to be included
    :arg to_date: end date for contributions to be included
    :arg locale: (optional) locale to filter on
    :arg product: (optional) only count documents for a product
    """
    return User.objects.filter(
        id__in=_active_contributors_id(from_date, to_date, locale, product)
    ).order_by("username")


def generate_short_url(long_url):
    """Return a shortned URL for a given long_url via bitly's API.

    :arg long_url: URL to shorten
    """

    # Check for empty credentials.
    if not settings.BITLY_ACCESS_TOKEN:
        return ""

    keys = {
        "long_url": long_url,
        "group_guid": settings.BITLY_GUID,
    }
    headers = {"Authorization": f"Bearer {settings.BITLY_ACCESS_TOKEN}"}

    resp = requests.post(url=settings.BITLY_API_URL, json=keys, headers=headers)
    resp.raise_for_status()

    return resp.json().get("link", "")


def num_active_contributors(from_date, to_date=None, locale=None, product=None):
    """Return number of active KB contributors for the specified parameters.

    An active KB contributor is a user that has created or reviewed a
    Revision in the given time period.

    :arg from_date: start date for contributions to be included
    :arg to_date: end date for contributions to be included
    :arg locale: (optional) locale to filter on
    :arg product: (optional) only count documents for a product
    """
    return len(_active_contributors_id(from_date, to_date, locale, product))


def _active_contributors_id(from_date, to_date, locale, product):
    """Return the set of ids for the top contributors based on the params.

    An active KB contributor is a user that has created or reviewed a
    Revision in the given time period.

    :arg from_date: start date for contributions to be included
    :arg to_date: end date for contributions to be included
    :arg locale: (optional) locale to filter on
    :arg product: (optional) only count documents for a product
    """
    editors = (
        Revision.objects.filter(created__gte=from_date, created__lt=to_date or Now())
        .values_list("creator", flat=True)
        .distinct()
    )

    reviewers = (
        Revision.objects.filter(reviewed__gte=from_date, reviewed__lt=to_date or Now())
        .values_list("reviewer", flat=True)
        .distinct()
    )

    if locale:
        editors = editors.filter(document__locale=locale)
        reviewers = reviewers.filter(document__locale=locale)

    if product:
        editors = editors.filter(
            Q(document__products=product) | Q(document__parent__products=product)
        )
        reviewers = reviewers.filter(
            Q(document__products=product) | Q(document__parent__products=product)
        )

    return set(list(editors) + list(reviewers))


def get_featured_articles(product=None, topics=None, locale=settings.WIKI_DEFAULT_LANGUAGE):
    """Returns up to 4 random articles from the most visited.

    Args:
        product: Optional product to filter by
        topics: Optional iterable of topics to filter by
        locale: Locale to get articles for, defaults to WIKI_DEFAULT_LANGUAGE
    """
    parent_prefix = "parent__" if locale != settings.WIKI_DEFAULT_LANGUAGE else ""

    filter_kwargs = {
        f"{parent_prefix}restrict_to_groups__isnull": True,
    }

    if product:
        filter_kwargs[f"{parent_prefix}products"] = product

    if topics:
        filter_kwargs[f"{parent_prefix}topics__in"] = topics

    excluded_product_slugs = settings.EXCLUDE_PRODUCT_SLUGS_FEATURED_ARTICLES

    qs = (
        Document.objects.filter(
            locale=locale,
            is_template=False,
            is_archived=False,
            current_revision__isnull=False,
            **filter_kwargs,
        )
        .exclude(**{f"{parent_prefix}products__slug__in": excluded_product_slugs})
        .exclude(html__startswith=REDIRECT_HTML)
        .select_related("current_revision")
        .annotate(
            num_visits=Subquery(
                WikiDocumentVisits.objects.filter(
                    document=OuterRef(f"{parent_prefix}pk"), period=LAST_7_DAYS
                ).values("visits")
            )
        )
        .exclude(num_visits__isnull=True)
        .order_by("-num_visits")
    )

    if topics:
        # Documents that match multiple topics will be repeated,
        # so remove any duplicates when we're matching by topics.
        qs = qs.distinct()

    # Only include the ten most visited articles for sampling.
    docs = list(qs[:10])

    if len(docs) <= 4:
        return docs
    return random.sample(docs, 4)


def get_visible_document_or_404(
    user, look_for_translation_via_parent=False, return_parent_if_no_translation=False, **kwargs
):
    """
    Get the document specified by the keyword arguments and visible to the given user, or 404.
    """

    try:
        return Document.objects.get_visible(user, **kwargs)
    except Document.DoesNotExist:
        pass

    if not (look_for_translation_via_parent and (locale := kwargs.get("locale"))):
        raise Http404

    # Make the same query without the locale.
    other_docs_qs = Document.objects.visible(
        user, **{k: v for k, v in kwargs.items() if k != "locale"}
    ).select_related("parent")

    for doc in other_docs_qs:
        base_doc = doc.parent or doc
        if base_doc.locale == locale:
            return base_doc
        elif (base_doc.locale == settings.WIKI_DEFAULT_LANGUAGE) and (
            translation := base_doc.translated_to(locale, visible_for_user=user)
        ):
            return translation

    if not (return_parent_if_no_translation and (locale != settings.WIKI_DEFAULT_LANGUAGE)):
        raise Http404

    kwargs["locale"] = settings.WIKI_DEFAULT_LANGUAGE
    try:
        return Document.objects.get_visible(user, **kwargs)
    except Document.DoesNotExist:
        raise Http404


def get_visible_revision_or_404(user, **kwargs):
    return get_object_or_404(Revision.objects.visible(user, **kwargs))


def build_topics_data(request: HttpRequest, product: Product, topics: list[Topic]) -> list[dict]:
    """Build topics_data for use in topic cards
    Args:
        request: HttpRequest - The current request
        product: Product - The product to get topics for
        topics: list[Topic] - List of topics to process
    Returns:
        list[dict]: List of topic data dictionaries containing:
            - topic: Topic object
            - topic_url: URL to topic's documents
            - title: Topic title
            - total_articles: Combined count of main and fallback articles
            - image_url: Topic image URL
            - documents: Up to 3 documents to display
    """
    topics_data: list[dict] = []

    featured_articles = get_featured_articles(product, locale=request.LANGUAGE_CODE, topics=topics)

    # Get both main and fallback documents from the faceted search
    main_docs_data, fallback_docs_data = documents_for(
        request.user, request.LANGUAGE_CODE, topics=topics, products=[product]
    )

    main_doc_ids = {doc["id"] for doc in main_docs_data}
    fallback_doc_ids = {doc["id"] for doc in (fallback_docs_data or [])}

    all_documents = (
        Document.objects.filter(id__in=main_doc_ids | fallback_doc_ids)
        .select_related("parent")
        .prefetch_related(
            "topics",
            "parent__topics",
        )
    )

    # topic_id -> (main_docs, fallback_docs) mapping
    topic_docs_map: dict[int, tuple[list[Document], list[Document]]] = {
        topic.id: ([], []) for topic in topics
    }
    doc_topics_map: dict[int, list[Topic]] = {}

    for doc in all_documents:
        doc_topics = set(doc.parent.topics.all()) if doc.parent else set(doc.topics.all())

        doc_topics_map[doc.id] = list(doc_topics)
        for topic in doc_topics:
            if topic.id in topic_docs_map:
                main_list, fallback_list = topic_docs_map[topic.id]
                target_list = main_list if doc.id in main_doc_ids else fallback_list
                target_list.append(doc)

    for topic in topics:
        main_topic_docs, fallback_topic_docs = topic_docs_map[topic.id]

        if not main_topic_docs and not fallback_topic_docs:
            continue

        topic_featured = [
            doc
            for doc in featured_articles
            if doc.id in doc_topics_map and any(t.id == topic.id for t in doc_topics_map[doc.id])
        ]

        # Get remaining main documents excluding featured ones
        remaining_docs = (doc for doc in main_topic_docs if doc not in topic_featured)

        # First try to get documents from featured and main docs
        main_docs = list(islice(chain(topic_featured, remaining_docs), 3))

        # Fall back to fallback documents only if no main documents exist
        documents_to_show = main_docs if main_docs else list(islice(fallback_topic_docs, 3))

        topic_data = {
            "topic": topic,
            "topic_url": reverse("products.documents", args=[product.slug, topic.slug]),
            "title": topic.title,
            "total_articles": len(main_topic_docs) + len(fallback_topic_docs),
            "image_url": topic.image_url,
            "documents": documents_to_show,
        }
        topics_data.append(topic_data)

    return topics_data


def remove_expired_from_kb_visited(
    session: SessionBase, ttl: int = KB_VISITED_DEFAULT_TTL
) -> None:
    """
    Remove expired visits (KB article URL's and their timestamps) from the
    "kb-visited" dictionary within the given session based on the given TTL.
    """
    if not (session and ("kb-visited" in session)):
        return

    now = time.time()
    kb_visited = session["kb-visited"]

    empty_keys = []
    for key, visits in kb_visited.items():
        # Remove any visits that have expired within this products-topics key.
        if expired_visits := [url for url, ts in visits.items() if (now - ts) > ttl]:
            for url in expired_visits:
                del visits[url]
            if not visits:
                # If there are no more visits under this key,
                # add it to the list of keys to remove.
                empty_keys.append(key)
            session.modified = True

    # Remove keys that no longer contain any slugs.
    for key in empty_keys:
        del kb_visited[key]


def update_kb_visited(
    session: SessionBase, doc: Document, ttl: int = KB_VISITED_DEFAULT_TTL
) -> None:
    """
    Updates the "kb-visited" dictionary within the given session, and also
    removes any visits that have expired based on the given TTL.
    """
    if not session:
        return

    remove_expired_from_kb_visited(session, ttl=ttl)

    kb_visited = session.setdefault("kb-visited", {})

    product_slugs = doc.get_products().order_by("slug").values_list("slug", flat=True)
    topic_slugs = doc.get_topics().order_by("slug").values_list("slug", flat=True)
    key = f"/{'/'.join(product_slugs)}/{'/'.join(topic_slugs)}/"

    url = doc.get_absolute_url()

    kb_visited.setdefault(key, {})[url] = time.time()
    session.modified = True


def has_visited_kb(
    session: SessionBase,
    product: Product,
    topic: Topic | None = None,
    ttl: int = KB_VISITED_DEFAULT_TTL,
) -> bool:
    """
    Return a boolean indicating whether or not the user has visited at least one
    KB article associated with the given product and, optionally, topic, within
    the given TTL.
    """
    if not (session and ("kb-visited" in session)):
        return False

    remove_expired_from_kb_visited(session, ttl=ttl)

    return any(
        (f"/{product.slug}/" in key) and ((topic is None) or (f"/{topic.slug}/" in key))
        for key in session["kb-visited"].keys()
    )


def get_kb_visited(
    session: SessionBase,
    product: Product,
    topic: Topic | None = None,
    ttl: int = KB_VISITED_DEFAULT_TTL,
) -> list[str]:
    """
    Return the KB articles (as a list of document URL's) visited by the user that are
    associated with the given product and, optionally, topic, within the given TTL.
    """
    if not (session and ("kb-visited" in session)):
        return []

    remove_expired_from_kb_visited(session, ttl=ttl)

    urls = []
    for key, visits in session["kb-visited"].items():
        if (f"/{product.slug}/" in key) and ((topic is None) or (f"/{topic.slug}/" in key)):
            urls.extend(visits.keys())

    return urls
