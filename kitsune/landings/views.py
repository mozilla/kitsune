from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import never_cache

from mobility.decorators import mobile_template

from kitsune.products.models import Product
from kitsune.sumo.parser import get_object_fallback
from kitsune.sumo.views import redirect_to
from kitsune.topics.models import Topic
from kitsune.wiki.facets import documents_for
from kitsune.wiki.models import Document


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
    moz_news = get_object_fallback(
        Document, MOZILLA_NEWS_DOC, request.LANGUAGE_CODE)

    return render(request, 'landings/home.html', {
        'products': products,
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


def hot_topics(request):
    """The hot topics landing page."""
    topic = get_object_or_404(Topic, slug='hot')

    data = dict(topic=topic)
    docs, fallback = documents_for(
        locale=request.LANGUAGE_CODE, topics=[topic])
    data.update(documents=docs, fallback_documents=fallback)

    return render(request, 'landings/hot.html', data)
