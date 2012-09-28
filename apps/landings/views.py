from django.views.decorators.cache import never_cache

import jingo
from mobility.decorators import mobile_template

from products.models import Product
from sumo.parser import get_object_fallback
from sumo.views import redirect_to
from topics.models import Topic, HOT_TOPIC_SLUG
from wiki.facets import documents_for
from wiki.models import Document
from wiki.views import SHOWFOR_DATA


# Docs for the mobile optimized templates:
HOME_DOCS_FOR_MOBILE = {
    'common': 'Desktop home for mobile - Common Questions',
    'top': 'Home page - Top'}
MOBILE_DOCS_FOR_MOBILE = {
    'common': 'Mobile home for mobile - Common Questions',
    'top': 'Mobile home - Top'}
SYNC_DOCS_FOR_MOBILE = {
    'common': 'Sync home for mobile - Common Questions',
    'top': 'Sync home - Top'}
MARKETPLACE_DOCS_FOR_MOBILE = {
    'common': 'Marketplace home for mobile - Common Questions',
    'top': 'Marketplace home - Top'}
FIREFOX_DOCS_FOR_MOBILE = {
    'common': 'Firefox home for mobile - Common Questions',
    'top': 'Firefox home - Top'}
PRODUCTS_DOCS_FOR_MOBILE = {
    'common': 'Products home for mobile - Common Questions',
    'top': 'Products home - Top'}
KB_DOCS_FOR_MOBILE = {
    'common': 'KB home for mobile - Common Questions',
    'top': 'KB home - Top'}
ASK_DOCS_FOR_MOBILE = {
    'common': 'Ask home for mobile - Common Questions',
    'top': 'Ask home - Top'}
PARTICIPATE_DOCS_FOR_MOBILE = {
    'common': 'Participate home for mobile - Common Questions',
    'top': 'Participate home - Top'}
FEEDBACK_DOCS_FOR_MOBILE = {
    'common': 'Feedback home for mobile - Common Questions',
    'top': 'Feedback home - Top'}


# Docs for the new IA:
MOZILLA_NEWS_DOC = 'Mozilla News'


@never_cache
def desktop_or_mobile(request):
    """Redirect mobile browsers to /mobile and others to /home."""
    url_name = 'home.mobile' if request.MOBILE else 'home'
    return redirect_to(request, url_name, permanent=False)


def home(request):
    """The home page."""
    if request.MOBILE:
        return old_home(request)

    products = Product.objects.filter(visible=True)
    topics = Topic.objects.filter(visible=True)
    moz_news = get_object_fallback(
        Document, MOZILLA_NEWS_DOC, request.locale)

    try:
        hot_docs, fallback_hot_docs = documents_for(
            locale=request.locale,
            topics=[Topic.objects.get(slug=HOT_TOPIC_SLUG)])
    except Topic.DoesNotExist:
        # "hot" topic doesn't exist, move on.
        hot_docs = fallback_hot_docs = None

    return jingo.render(request, 'landings/home.html', {
        'products': products,
        'topics': topics,
        'hot_docs': hot_docs,
        'fallback_hot_docs': fallback_hot_docs,
        'moz_news': moz_news})


@mobile_template('landings/{mobile/}old-home.html')
def old_home(request, template=None):
    docs = HOME_DOCS_FOR_MOBILE
    return jingo.render(request, template,
                        _data(docs, request.locale, 'firefox', 'desktop'))


@mobile_template('landings/{mobile/}mobile.html')
def mobile(request, template=None):
    if not request.MOBILE:
        return redirect_to(
            request, 'products.product', slug='mobile', permanent=False)

    docs = MOBILE_DOCS_FOR_MOBILE
    return jingo.render(request, template,
                        _data(docs, request.locale, 'mobile', 'mobile'))


@mobile_template('landings/{mobile/}sync.html')
def sync(request, template=None):
    if not request.MOBILE:
        return redirect_to(request, 'home', permanent=False)

    docs = SYNC_DOCS_FOR_MOBILE
    return jingo.render(request, template,
                        _data(docs, request.locale))


@mobile_template('landings/{mobile/}marketplace.html')
def marketplace(request, template=None):
    if not request.MOBILE:
        return redirect_to(request, 'home', permanent=False)

    docs = MARKETPLACE_DOCS_FOR_MOBILE
    # Marketplace search results should only be kb (zendesk is being
    # used for questions).
    return jingo.render(request, template,
                        _data(docs, request.locale, only_kb=True))


@mobile_template('landings/{mobile/}firefox.html')
def firefox(request, template=None):
    if not request.MOBILE:
        return redirect_to(
            request, 'products.product', slug='firefox', permanent=False)

    docs = FIREFOX_DOCS_FOR_MOBILE
    return jingo.render(request, template,
                        _data(docs, request.locale, 'firefox', 'desktop'))


@mobile_template('landings/{mobile/}products.html')
def old_products(request, template=None):
    docs = PRODUCTS_DOCS_FOR_MOBILE
    return jingo.render(request, template,
                        _data(docs, request.locale))


@mobile_template('landings/{mobile/}kb.html')
def old_kb(request, template=None):
    docs = KB_DOCS_FOR_MOBILE
    return jingo.render(request, template,
                        _data(docs, request.locale))


@mobile_template('landings/{mobile/}ask.html')
def ask(request, template=None):
    if not request.MOBILE:
        return redirect_to(
            request,
            'wiki.document',
            document_slug='get-community-support',
            permanent=False)

    docs = ASK_DOCS_FOR_MOBILE
    return jingo.render(request, template,
                        _data(docs, request.locale))


@mobile_template('landings/{mobile/}participate.html')
def participate(request, template=None):
    if not request.MOBILE:
        return redirect_to(
            request,
            'wiki.document',
            document_slug='superheroes-wanted',
            permanent=False)

    docs = PARTICIPATE_DOCS_FOR_MOBILE
    return jingo.render(request, template,
                        _data(docs, request.locale))


@mobile_template('landings/{mobile/}feedback.html')
def feedback(request, template=None):
    if not request.MOBILE:
        return redirect_to(
            request,
            'wiki.document',
            document_slug='suggestion-box',
            permanent=False)

    docs = FEEDBACK_DOCS_FOR_MOBILE
    return jingo.render(request, template,
                        _data(docs, request.locale))


def integrity_check(request):
    return jingo.render(request, 'landings/integrity-check.html')


def _data(docs, locale, product=None, q_tags=None, only_kb=False):
    """Add the documents and showfor data to the context data."""
    data = {}
    for side, title in docs.iteritems():
        data[side] = get_object_fallback(Document, title, locale)

    data.update(SHOWFOR_DATA)

    if product:
        data.update(search_params={'product': product})

    if only_kb:
        data.setdefault('search_params', {}).update({'w': 1})
    elif q_tags:
        data['search_params'].update(q_tags=q_tags)

    return data
