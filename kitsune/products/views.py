import json
from datetime import datetime, timedelta

from django.db.models import OuterRef, Q, Subquery
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from product_details import product_details

from kitsune.products.models import Product, Topic, TopicSlugHistory
from kitsune.questions import config as aaq_config
from kitsune.sumo import NAVIGATION_TOPICS
from kitsune.wiki.decorators import check_simple_wiki_locale
from kitsune.wiki.facets import documents_for, topics_for
from kitsune.wiki.models import Revision
from kitsune.wiki.utils import get_featured_articles


@check_simple_wiki_locale
def product_list(request):
    """The product picker page."""
    template = "products/products.html"
    products = Product.active.filter(visible=True)
    return render(request, template, {"products": products})


def _get_aaq_product_key(slug):
    product_key = ""
    for k, v in aaq_config.products.items():
        if isinstance(v, dict):
            if v.get("product") == slug:
                product_key = k
    return product_key or None


@check_simple_wiki_locale
def product_landing(request, slug):
    """The product landing page."""
    if slug == "firefox-accounts":
        return redirect(product_landing, slug="mozilla-account", permanent=True)

    product = get_object_or_404(Product, slug=slug)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        # Return a list of topics/subtopics for the product
        topic_list = list()
        for t in Topic.active.filter(product=product, visible=True):
            topic_list.append({"id": t.id, "title": t.title})
        return HttpResponse(json.dumps({"topics": topic_list}), content_type="application/json")

    if slug == "firefox":
        latest_version = product_details.firefox_versions["LATEST_FIREFOX_VERSION"]
    else:
        versions = product.versions.filter(default=True)
        if versions:
            latest_version = versions[0].min_version
        else:
            latest_version = 0

    return render(
        request,
        "products/product.html",
        {
            "product_key": _get_aaq_product_key(product.slug),
            "product": product,
            "products": Product.active.filter(visible=True),
            "topics": topics_for(request.user, product=product, parent=None),
            "search_params": {"product": slug},
            "latest_version": latest_version,
            "featured": get_featured_articles(product, locale=request.LANGUAGE_CODE),
        },
    )


@check_simple_wiki_locale
def document_listing(request, topic_slug, product_slug=None, subtopic_slug=None):
    """The document listing page for a product + topic."""

    topic_navigation = any(
        [
            request.resolver_match.url_name == "products.topic_documents",
            request.resolver_match.url_name == "products.topic_product_documents",
            topic_slug and not product_slug,
        ]
    )

    if topic_slug:
        try:
            old_topic_slug = TopicSlugHistory.objects.get(
                Q(slug=topic_slug) | Q(slug=subtopic_slug)
            )
            redirect_params = {
                "topic_slug": old_topic_slug.topic.slug,
            }

            if product_slug:
                redirect_params["product_slug"] = product_slug

            return redirect(document_listing, **redirect_params)
        except TopicSlugHistory.DoesNotExist:
            ...
        except TopicSlugHistory.MultipleObjectsReturned:
            ...

    product = None
    if product_slug:
        product = get_object_or_404(Product, slug=product_slug)
        request.session["aaq_context"] = {
            "has_ticketing_support": product.has_ticketing_support,
            "key": _get_aaq_product_key(product_slug),
            "has_public_forum": product.questions_enabled(locale=request.LANGUAGE_CODE),
        }

    doc_kw = {
        "locale": request.LANGUAGE_CODE,
        "products": [product] if product else None,
    }
    subtopic = None
    topic_list = []
    topic_kw = {
        "slug": topic_slug,
        "parent__isnull": True,
        "visible": True,
    }

    if topic_navigation:
        topics = Topic.active.filter(**topic_kw)
        topic_subquery = (
            Topic.active.filter(slug__in=NAVIGATION_TOPICS)
            .filter(slug=OuterRef("slug"))
            .order_by("id")
            .values("id")[:1]
        )
        topic_list = Topic.active.filter(id__in=Subquery(topic_subquery))
        doc_kw["topics"] = topics
        topic = get_object_or_404(topic_list, slug=topic_slug)
    else:
        topic = get_object_or_404(Topic, slug=topic_slug, product=product, parent__isnull=True)
        topics = topics_for(request.user, product=product, parent=None)

        doc_kw["topics"] = [topic]
        if subtopic_slug is not None:
            subtopic = get_object_or_404(Topic, slug=subtopic_slug, product=product, parent=topic)
            doc_kw["topics"] = [subtopic]

    if not topics.exists():
        raise Http404
    template = "products/documents.html"

    documents, fallback_documents = documents_for(request.user, **doc_kw)

    thirty_days_ago = datetime.now() - timedelta(days=30)
    for document in documents:
        document["is_past_thirty_days"] = document["created"] < thirty_days_ago
        document["is_first_revision"] = (
            Revision.objects.filter(document=document["id"], is_approved=True).count() == 1
        )

    return render(
        request,
        template,
        {
            "product": product,
            "topic": topic,
            "subtopic": subtopic,
            "topics": topics,
            "subtopics": topics_for(request.user, product=product, parent=topic),
            "documents": documents,
            "fallback_documents": fallback_documents,
            "search_params": {"product": product_slug},
            "topic_navigation": topic_navigation,
            "topic_list": topic_list,
            "products": Product.active.filter(topics__in=topics),
        },
    )
