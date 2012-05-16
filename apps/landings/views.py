from django.views.decorators.cache import never_cache

import jingo
from mobility.decorators import mobile_template

from sumo.parser import get_object_fallback
from sumo.views import redirect_to
from wiki.models import Document
from wiki.views import SHOWFOR_DATA


HOME_DOCS = {
    'quick': 'Home page - Quick',
    'explore': 'Home page - Explore',
    'top': 'Home page - Top'}
MOBILE_DOCS = {
    'quick': 'Mobile home - Quick',
    'explore': 'Mobile home - Explore',
    'top': 'Mobile home - Top'}
SYNC_DOCS = {
    'quick': 'Sync home - Quick',
    'explore': 'Sync home - Explore',
    'top': 'Sync home - Top'}
FXHOME_DOCS = {
    'quick': 'FxHome home - Quick',
    'explore': 'FxHome home - Explore',
    'top': 'FxHome home - Top'}
MARKETPLACE_DOCS = {
    'quick': 'Marketplace home - Quick',
    'explore': 'Marketplace home - Explore',
    'top': 'Marketplace home - Top'}
FIREFOX_DOCS = {
    'quick': 'Firefox home - Quick',
    'explore': 'Firefox home - Explore',
    'top': 'Firefox home - Top'}
PRODUCTS_DOCS = {
    'quick': 'Products home - Quick',
    'explore': 'Products home - Explore',
    'top': 'Products home - Top'}
KB_DOCS = {
    'quick': 'KB home - Quick',
    'explore': 'KB home - Explore',
    'top': 'KB home - Top'}
ASK_DOCS = {
    'quick': 'Ask home - Quick',
    'explore': 'Ask home - Explore',
    'top': 'Ask home - Top'}
PARTICIPATE_DOCS = {
    'quick': 'Participate home - Quick',
    'explore': 'Participate home - Explore',
    'top': 'Participate home - Top'}
FEEDBACK_DOCS = {
    'quick': 'Feedback home - Quick',
    'explore': 'Feedback home - Explore',
    'top': 'Feedback home - Top'}
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
FXHOME_DOCS_FOR_MOBILE = {
    'common': 'FxHome home for mobile - Common Questions',
    'top': 'FxHome home - Top'}
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


@never_cache
def desktop_or_mobile(request):
    """Redirect mobile browsers to /mobile and others to /home."""
    url_name = 'home.mobile' if request.MOBILE else 'home'
    return redirect_to(request, url_name, permanent=False)


@mobile_template('landings/{mobile/}home.html')
def home(request, template=None):
    docs = HOME_DOCS_FOR_MOBILE if request.MOBILE else HOME_DOCS
    return jingo.render(request, template,
                        _data(docs, request.locale, 'desktop'))


@mobile_template('landings/{mobile/}mobile.html')
def mobile(request, template=None):
    docs = MOBILE_DOCS_FOR_MOBILE if request.MOBILE else MOBILE_DOCS
    return jingo.render(request, template,
                        _data(docs, request.locale, 'mobile'))


@mobile_template('landings/{mobile/}sync.html')
def sync(request, template=None):
    docs = SYNC_DOCS_FOR_MOBILE if request.MOBILE else SYNC_DOCS
    return jingo.render(request, template,
                        _data(docs, request.locale, 'sync'))


@mobile_template('landings/{mobile/}fxhome.html')
def fxhome(request, template=None):
    docs = FXHOME_DOCS_FOR_MOBILE if request.MOBILE else FXHOME_DOCS
    return jingo.render(request, template,
                        _data(docs, request.locale, 'FxHome'))


@mobile_template('landings/{mobile/}marketplace.html')
def marketplace(request, template=None):
    docs = MARKETPLACE_DOCS_FOR_MOBILE if request.MOBILE else MARKETPLACE_DOCS
    # Marketplace search results should only be kb (zendesk is being
    # used for questions).
    return jingo.render(request, template,
                        _data(docs, request.locale, 'marketplace', True))


@mobile_template('landings/{mobile/}firefox.html')
def firefox(request, template=None):
    docs = FIREFOX_DOCS_FOR_MOBILE if request.MOBILE else FIREFOX_DOCS
    return jingo.render(request, template,
                        _data(docs, request.locale, 'desktop'))


@mobile_template('landings/{mobile/}products.html')
def products(request, template=None):
    docs = PRODUCTS_DOCS_FOR_MOBILE if request.MOBILE else PRODUCTS_DOCS
    return jingo.render(request, template,
                        _data(docs, request.locale))


@mobile_template('landings/{mobile/}kb.html')
def kb(request, template=None):
    docs = KB_DOCS_FOR_MOBILE if request.MOBILE else KB_DOCS
    return jingo.render(request, template,
                        _data(docs, request.locale))


@mobile_template('landings/{mobile/}ask.html')
def ask(request, template=None):
    docs = ASK_DOCS_FOR_MOBILE if request.MOBILE else ASK_DOCS
    return jingo.render(request, template,
                        _data(docs, request.locale))


@mobile_template('landings/{mobile/}participate.html')
def participate(request, template=None):
    docs = PARTICIPATE_DOCS_FOR_MOBILE if request.MOBILE else PARTICIPATE_DOCS
    return jingo.render(request, template,
                        _data(docs, request.locale))


@mobile_template('landings/{mobile/}feedback.html')
def feedback(request, template=None):
    docs = FEEDBACK_DOCS_FOR_MOBILE if request.MOBILE else FEEDBACK_DOCS
    return jingo.render(request, template,
                        _data(docs, request.locale))


def integrity_check(request):
    return jingo.render(request, 'landings/integrity-check.html')


def reminder(request):
    """MozCamp landing page for people to sign up to contribute."""
    return jingo.render(request, 'landings/reminder.html')


def _data(docs, locale, product=None, only_kb=False):
    """Add the documents and showfor data to the context data."""
    data = {}
    for side, title in docs.iteritems():
        data[side] = get_object_fallback(Document, title, locale)

    data.update(SHOWFOR_DATA)

    if product:
        data.update(search_params={'product': product})

    if only_kb:
        data['search_params'].update(w=1)
    elif product:
        data['search_params'].update(q_tags=product)

    return data
