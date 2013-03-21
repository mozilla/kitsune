from django.shortcuts import render
from django.views.decorators.cache import never_cache

from mobility.decorators import mobile_template
from products.models import Product
from sumo.parser import get_object_fallback
from sumo.views import redirect_to
from topics.models import Topic, HOT_TOPIC_SLUG
from wiki.facets import documents_for
from wiki.models import Document


# Docs for the new IA:
MOZILLA_NEWS_DOC = 'Mozilla News'


@never_cache
def desktop_or_mobile(request):
    """Redirect mobile browsers to /mobile and others to /home."""
    mobile = 'products'
    url_name = mobile if request.MOBILE else 'home'
    return redirect_to(request, url_name, permanent=False)


def home(request):
    """The home page."""
    if request.MOBILE:
        return redirect_to(request, 'products', permanent=False)

    products = Product.objects.filter(visible=True)
    topics = Topic.objects.filter(visible=True)
    moz_news = get_object_fallback(
        Document, MOZILLA_NEWS_DOC, request.LANGUAGE_CODE)

    try:
        hot_docs, fallback_hot_docs = documents_for(
            locale=request.LANGUAGE_CODE,
            topics=[Topic.objects.get(slug=HOT_TOPIC_SLUG)])
    except Topic.DoesNotExist:
        # "hot" topic doesn't exist, move on.
        hot_docs = fallback_hot_docs = None

    return render(request, 'landings/home.html', {
        'products': products,
        'topics': topics,
        'hot_docs': hot_docs,
        'fallback_hot_docs': fallback_hot_docs,
        'moz_news': moz_news})


@mobile_template('landings/{mobile/}get-involved.html')
def get_involved(request, template):
    return render(request, template)


@mobile_template('landings/{mobile/}get-involved-aoa.html')
def get_involved_aoa(request, template):
    return render(request, template)


@mobile_template('landings/{mobile/}get-involved-questions.html')
def get_involved_questions(request, template):
    return render(request, template)


@mobile_template('landings/{mobile/}get-involved-kb.html')
def get_involved_kb(request, template):
    return render(request, template)


@mobile_template('landings/{mobile/}get-involved-l10n.html')
def get_involved_l10n(request, template):
    return render(request, template)


def integrity_check(request):
    return render(request, 'landings/integrity-check.html')
