import random

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Prefetch, Q
from django.db.models.functions import Now
from django.http import Http404
from django.shortcuts import get_object_or_404

from kitsune.dashboards import LAST_7_DAYS
from kitsune.dashboards.models import WikiDocumentVisits
from kitsune.sumo.urlresolvers import reverse
from kitsune.wiki.models import Document, Revision
from kitsune.wiki.facets import documents_for


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


def get_featured_articles(product=None, locale=settings.WIKI_DEFAULT_LANGUAGE, topic=None):
    """Returns 4 random articles from the most visited.

    If a product is passed, it returns 4 random highly visited articles from that product.
    If a topic is passed, it returns 4 random highly visited articles from that topic.
    """
    visits = (
        WikiDocumentVisits.objects.filter(period=LAST_7_DAYS)
        .filter(
            document__restrict_to_groups__isnull=True,
            document__locale=settings.WIKI_DEFAULT_LANGUAGE,
        )
        .exclude(document__products__slug__in=settings.EXCLUDE_PRODUCT_SLUGS_FEATURED_ARTICLES)
        .exclude(document__is_archived=True)
        .exclude(document__is_template=True)
        .order_by("-visits")
        .select_related("document")
    )

    if product:
        visits = visits.filter(document__products__in=[product.id])

    if topic:
        visits = visits.filter(document__topics__in=[topic.id])

    visits = visits[:10]
    documents = []

    if locale == settings.WIKI_DEFAULT_LANGUAGE:
        for visit in visits:
            documents.append(visit.document)
    else:
        # prefretch localised documents to avoid n+1 problem
        visits = visits.prefetch_related(
            Prefetch(
                "document__translations",
                queryset=Document.objects.visible(
                    locale=locale,
                    current_revision__is_approved=True,
                    is_archived=False,
                    is_template=False,
                ),
            )
        )

        for visit in visits:
            translation = visit.document.translations.first()
            if not translation:
                continue
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


def build_topics_data(request, product, topics):
    """Build topics_data for use in topic cards"""
    topics_data = []

    # Get all documents for all topics up front
    all_docs, _ = documents_for(
        request.user, request.LANGUAGE_CODE, topics=list(topics), products=[product]
    )

    # Convert all docs to Document objects
    doc_ids = [doc["id"] for doc in all_docs]
    documents = Document.objects.filter(id__in=doc_ids)

    # Create a mapping of Document objects to their topics from all_docs
    for doc_dict in all_docs:
        for doc in documents:
            if doc.id == doc_dict["id"]:
                doc.topics_list = doc_dict.get("topics", [])
                break

    for topic in topics:
        # Get featured articles first (returns up to 4 Document objects)
        featured_articles = get_featured_articles(
            product, locale=request.LANGUAGE_CODE, topic=topic
        )

        # Get docs for this topic from documents
        topic_docs = [doc for doc in documents if topic.id in getattr(doc, "topics_list", [])]

        # Only query for additional docs if we need more to reach 3
        if len(featured_articles) < 3:
            # If we don't have enough featured articles, append more from topic_docs
            remaining_docs = [doc for doc in topic_docs if doc not in featured_articles]
            featured_articles.extend(remaining_docs)

        topic_data = {
            "topic": topic,
            "topic_url": reverse("products.documents", args=[product.slug, topic.slug]),
            "title": topic.title,
            "total_articles": len(topic_docs),
            "image_url": topic.image_url,
            "documents": featured_articles[:3],
        }
        topics_data.append(topic_data)

    return topics_data
