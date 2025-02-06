import random
from itertools import chain, islice

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Prefetch, Q
from django.db.models.functions import Now
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404

from kitsune.dashboards import LAST_7_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.products.models import Product, Topic
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.facets import documents_for
from kitsune.wiki.models import Document, Revision


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
    """Returns up to 4 random articles per topic from the most visited.

    Args:
        product: Optional product to filter by
        topics: Optional iterable of topics to filter by
        locale: Locale to get articles for, defaults to WIKI_DEFAULT_LANGUAGE
    """
    # Get base queryset with all needed relations in one hit
    visits = (
        WikiDocumentVisits.objects.filter(period=LAST_7_DAYS)
        .select_related("document")
        .prefetch_related(
            "document__products",
            "document__topics",
            Prefetch(
                "document__translations",
                queryset=(
                    Document.objects.visible(
                        locale=locale,
                        current_revision__is_approved=True,
                        is_archived=False,
                        is_template=False,
                    )
                    if locale != settings.WIKI_DEFAULT_LANGUAGE
                    else None
                ),
            ),
        )
        .filter(
            document__restrict_to_groups__isnull=True,
            document__locale=settings.WIKI_DEFAULT_LANGUAGE,
            document__is_archived=False,
            document__is_template=False,
        )
        .exclude(document__products__slug__in=settings.EXCLUDE_PRODUCT_SLUGS_FEATURED_ARTICLES)
    )

    # Add product and topics filters to the database query
    if product:
        visits = visits.filter(document__products=product)
    if topics:
        visits = visits.filter(document__topics__in=topics)

    # Order by visits but don't limit - we need enough documents for all topics
    visits = visits.order_by("-visits")

    # Get documents based on locale
    documents = []
    if locale == settings.WIKI_DEFAULT_LANGUAGE:
        documents = [visit.document for visit in visits]
    else:
        for visit in visits:
            translation = next(iter(visit.document.translations.all()), None)
            if translation:
                documents.append(translation)

    if len(documents) <= 4:
        return documents
    return random.sample(documents, 4)


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

    if (
        not look_for_translation_via_parent
        or not (locale := kwargs.get("locale"))
        or (locale == settings.WIKI_DEFAULT_LANGUAGE)
    ):
        # We either don't want to try to find the translation via its parent, or it doesn't
        # make sense, because we're not making a locale-specific request or the locale we're
        # requesting is already the default locale.
        raise Http404

    # We couldn't find a visible translation in the requested non-default locale, so let's
    # see if we can find a visible translation via its parent.
    kwargs.update(locale=settings.WIKI_DEFAULT_LANGUAGE)
    parent = get_object_or_404(Document.objects.visible(user, **kwargs))

    # If there's a visible translation of the parent for the requested locale, return it.
    if translation := parent.translated_to(locale, visible_for_user=user):
        return translation

    # Otherwise, we're left with the parent.
    if return_parent_if_no_translation:
        return parent

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
        doc_topics = set(doc.topics.all()) or (
            set(doc.parent.topics.all()) if doc.parent else set()
        )

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
