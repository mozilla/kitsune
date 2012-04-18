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


def integrity_check(request):
    return jingo.render(request, 'landings/integrity-check.html')


def reminder(request):
    """MozCamp landing page for people to sign up to contribute."""
    return jingo.render(request, 'landings/reminder.html')


def _data(docs, locale, product, only_kb=False):
    """Add the documents and showfor data to the context data."""
    data = {}
    for side, title in docs.iteritems():
        data[side] = get_object_fallback(Document, title, locale)

    data.update(SHOWFOR_DATA)
    data.update(search_params={'product': product})

    if only_kb:
        data['search_params'].update(w=1)
    else:
        data['search_params'].update(q_tags=product)

    return data
