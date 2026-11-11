from django.conf import settings
from django.db.models import Exists, OuterRef, Prefetch, Q
from django.db.models.functions import Coalesce, Lower
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from kitsune.products.models import Product, Topic
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import mark_private, paginate
from kitsune.wiki.config import DOCUMENTS_PER_PAGE, REDIRECT_HTML
from kitsune.wiki.models import Audience, Document, DocumentAudience
from kitsune.wiki.utils import group_by_visibility

RECENTLY_UPDATED_COUNT = 5
TOPIC_CARD_DOCUMENT_COUNT = 3


@require_GET
def knowledge_bases(request):
    """The directory of the knowledge bases listed for the user."""
    listed = list(Audience.objects.listed_for(request.user))
    shows_private = any(not knowledge_base.is_public for knowledge_base in listed)
    response = render(
        request,
        "wiki/knowledge_bases.html",
        {"sections": group_by_visibility(listed), "suppress_analytics": shows_private},
    )
    if shows_private:
        mark_private(response)
    return response


def _of_originals(original_ids):
    """Articles whose original is among the ids: the originals and their translations."""
    return Q(parent__isnull=True, id__in=original_ids) | Q(parent__in=original_ids)


def _original_ids(documents):
    return documents.values(original_id=Coalesce("parent_id", "id"))


def _readable_documents(user, locale, knowledge_base):
    """
    The knowledge base's articles the user can read in the locale, and the en-US originals
    that aren't translated into it, as topic listings do.
    """
    assigned = DocumentAudience.objects.filter(audience=knowledge_base).values("document_id")
    readable = (
        Document.objects.visible(
            user,
            permission_locale=locale,
            is_archived=False,
            current_revision__isnull=False,
            category__in=settings.IA_DEFAULT_CATEGORIES,
        )
        .filter(_of_originals(assigned))
        .exclude(html__startswith=REDIRECT_HTML)
    )
    in_locale = readable.filter(locale=locale)
    if locale == settings.WIKI_DEFAULT_LANGUAGE:
        return in_locale
    translated = in_locale.filter(parent=OuterRef("pk"))
    return in_locale | readable.filter(locale=settings.WIKI_DEFAULT_LANGUAGE).exclude(
        Exists(translated)
    )


@require_GET
def knowledge_base(request, slug):
    """
    A knowledge base's page: an overview, or with "topic" or "page" in the query, its article
    list. A knowledge base the user can't read is not found, exactly like an unknown slug.
    """
    knowledge_base = get_object_or_404(Audience.objects.browsable_by(request.user), slug=slug)
    locale = request.LANGUAGE_CODE
    documents = _readable_documents(request.user, locale, knowledge_base)
    page_url = reverse("wiki.knowledge_base", args=[knowledge_base.slug])
    topics = Topic.active.filter(visible=True, parent__isnull=True)

    scope = documents
    selected_topic = None
    if topic_slug := request.GET.get("topic"):
        tagged = Document.topics.through.objects.filter(topic__in=topics.filter(slug=topic_slug))
        scope = documents.filter(_of_originals(tagged.values("document_id")))
        selected_topic = topics.filter(
            id__in=tagged.filter(document_id__in=_original_ids(scope)).values("topic_id")
        ).first()
        if selected_topic is None:
            raise Http404

    products = list(
        Product.active.filter(
            id__in=Document.products.through.objects.filter(
                document_id__in=_original_ids(scope)
            ).values("product_id")
        ).order_by("display_order", Lower("title"))
    )
    selected_product = None
    if product_slug := request.GET.get("product"):
        selected_product = next((p for p in products if p.slug == product_slug), None)
        if selected_product is None:
            raise Http404
        with_product = Document.products.through.objects.filter(product=selected_product)
        scope = scope.filter(_of_originals(with_product.values("document_id")))

    list_mode = selected_topic is not None or "page" in request.GET
    context = {
        "knowledge_base": knowledge_base,
        "has_documents": documents.exists(),
        "list_mode": list_mode,
        "products": products if len(products) > 1 else [],
        "selected_product": selected_product,
        "selected_topic": selected_topic,
        "page_url": page_url,
        "suppress_analytics": not knowledge_base.is_public,
    }

    if list_mode:
        context["documents"] = paginate(
            request,
            scope.select_related("current_revision")
            .defer("html", "current_revision__content")
            .order_by(Lower("title"), "id"),
            per_page=DOCUMENTS_PER_PAGE,
        )
    else:
        featured_ids = list(knowledge_base.featured.values_list("document_id", flat=True))
        by_original = {
            document.original.id: document
            for document in documents.filter(_of_originals(featured_ids))
            .select_related("current_revision", "parent")
            .defer("html", "parent__html", "current_revision__content")
        }
        context["featured"] = [
            by_original[document_id] for document_id in featured_ids if document_id in by_original
        ]

        articles = list(
            scope.select_related("current_revision", "parent")
            .defer("html", "parent__html", "current_revision__content")
            .prefetch_related(
                Prefetch("topics", queryset=topics), Prefetch("parent__topics", queryset=topics)
            )
        )
        by_topic = {}
        for document in articles:
            document.kb_topics = list(document.original.topics.all())
            for topic in document.kb_topics:
                by_topic.setdefault(topic, []).append(document)

        topic_cards = []
        for topic in sorted(
            by_topic, key=lambda topic: (topic.display_order, topic.title.casefold())
        ):
            in_topic = sorted(
                by_topic[topic],
                key=lambda document: (
                    document.locale != locale,
                    document.original.display_order,
                    document.title.casefold(),
                ),
            )
            topic_cards.append(
                {
                    "topic": topic,
                    "topic_url": urlparams(
                        page_url,
                        topic=topic.slug,
                        product=selected_product.slug if selected_product else None,
                    ),
                    "title": topic.title,
                    "total_articles": len(in_topic),
                    "image_url": topic.image_url,
                    "documents": in_topic[:TOPIC_CARD_DOCUMENT_COUNT],
                }
            )
        context["topic_cards"] = topic_cards
        context["recent"] = sorted(
            articles, key=lambda document: document.current_revision.created, reverse=True
        )[:RECENTLY_UPDATED_COUNT]

    response = render(request, "wiki/knowledge_base.html", context)
    if not knowledge_base.is_public:
        mark_private(response)
    return response
