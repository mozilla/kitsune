import json

from django.conf import settings
from django.db.models import Exists, OuterRef, Q
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from product_details import product_details

from kitsune.flagit.views import get_hierarchical_topics
from kitsune.products import get_product_redirect_response
from kitsune.products.models import Product, Topic, TopicSlugHistory
from kitsune.sumo.utils import has_aaq_config, set_aaq_context
from kitsune.wiki.decorators import check_simple_wiki_locale
from kitsune.wiki.facets import documents_for, topics_for
from kitsune.wiki.models import Document, Revision
from kitsune.wiki.utils import build_topics_data, get_featured_articles


@check_simple_wiki_locale
def product_list(request):
    """The product picker page."""
    template = "products/products.html"
    products = Product.active.filter(visible=True)
    return render(request, template, {"products": products})


@check_simple_wiki_locale
def product_landing(request: HttpRequest, slug: str) -> HttpResponse:
    """The product landing page.

    Args:
        request: The HTTP request
        slug: Product slug identifier

    Returns:
        Rendered product landing page

    Raises:
        Http404: If product not found
    """
    redirect_response = get_product_redirect_response(slug, product_landing)
    if redirect_response:
        return redirect_response

    product = get_object_or_404(Product, slug=slug)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        # Return a list of topics/subtopics for the product
        topic_list = get_hierarchical_topics(product)
        return HttpResponse(json.dumps({"topics": topic_list}), content_type="application/json")

    if slug == "firefox":
        latest_version = product_details.firefox_versions["LATEST_FIREFOX_VERSION"]
    else:
        versions = product.versions.filter(default=True)
        if versions:
            latest_version = versions[0].min_version
        else:
            latest_version = 0
    topics = topics_for(request.user, product=product, parent=None)

    return render(
        request,
        "products/product.html",
        {
            "product": product,
            "products": Product.active.filter(visible=True),
            "topics": build_topics_data(request, product, topics),
            "search_params": {"product": slug},
            "latest_version": latest_version,
            "featured": get_featured_articles(product=product, locale=request.LANGUAGE_CODE),
            "has_aaq_config": has_aaq_config(product),
        },
    )


@check_simple_wiki_locale
def document_listing(request, topic_slug, product_slug=None, subtopic_slug=None):
    """The document listing page for a product + topic."""

    # Check for product slug aliases and redirect if needed
    redirect_response = get_product_redirect_response(
        product_slug, document_listing, topic_slug=topic_slug, subtopic_slug=subtopic_slug
    )
    if redirect_response:
        return redirect_response

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
                "permanent": True,
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
        set_aaq_context(request, product)

    doc_kw = {
        "locale": request.LANGUAGE_CODE,
        "products": [product] if product else None,
    }
    subtopic = None
    topic_list = []
    product_topics = []
    relevant_products = []
    topic_kw = {
        "slug": topic_slug,
        "visible": True,
    }

    if topic_navigation:
        try:
            topic = Topic.active.get(**topic_kw)
        except Topic.DoesNotExist:
            raise Http404
        except Topic.MultipleObjectsReturned:
            topic = Topic.active.filter(**topic_kw).first()

        topic_list = Topic.active.filter(in_nav=True)
        relevant_products = Product.active.filter(m2m_topics=topic).filter(
            Exists(
                Document.objects.visible(
                    is_archived=False,
                    topics=topic,
                    products=OuterRef("pk"),
                    locale=request.LANGUAGE_CODE,
                    category__in=settings.IA_DEFAULT_CATEGORIES,
                )
            )
        )
    else:
        topic = get_object_or_404(
            Topic.active, slug=topic_slug, products=product, parent__isnull=True
        )
        product_topics = topics_for(request.user, product=product, parent=None)

        if subtopic_slug is not None:
            subtopic = get_object_or_404(
                Topic.active, slug=subtopic_slug, products=product, parent=topic
            )
            doc_kw["topics"] = [subtopic]

    if not doc_kw.get("topics"):
        doc_kw["topics"] = [topic]
    template = "products/documents.html"

    documents, fallback_documents = documents_for(request.user, **doc_kw)

    for document in documents:
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
            "topics": product_topics,
            "subtopics": topics_for(request.user, product=product, parent=topic),
            "documents": documents,
            "fallback_documents": fallback_documents,
            "search_params": {"product": product_slug},
            "topic_navigation": topic_navigation,
            "topic_list": topic_list,
            "products": relevant_products,
        },
    )
