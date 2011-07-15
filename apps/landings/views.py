import jingo
from mobility.decorators import mobile_template

from sumo.parser import get_object_fallback
from wiki.models import Document
from wiki.views import SHOWFOR_DATA


HOME_DOCS = {'quick': 'Home page - Quick', 'explore': 'Home page - Explore',
             'top': 'Home page - Top'}
MOBILE_DOCS = {'quick': 'Mobile home - Quick',
               'explore': 'Mobile home - Explore',
               'top': 'Mobile home - Top'}
SYNC_DOCS = {'quick': 'Sync home - Quick', 'explore': 'Sync home - Explore',
             'top': 'Sync home - Top'}
FXHOME_DOCS = {'quick': 'FxHome home - Quick',
               'explore': 'FxHome home - Explore',
               'top': 'FxHome home - Top'}
HOME_DOCS_FOR_MOBILE = {'common':
                        'Desktop home for mobile - Common Questions',
                        'top': 'Home page - Top'}
MOBILE_DOCS_FOR_MOBILE = {'common':
                          'Mobile home for mobile - Common Questions',
                          'top': 'Mobile home - Top'}
SYNC_DOCS_FOR_MOBILE = {'common':
                        'Sync home for mobile - Common Questions',
                        'top': 'Sync home - Top'}
FXHOME_DOCS_FOR_MOBILE = {'common':
                          'FxHome home for mobile - Common Questions',
                          'top': 'FxHome home - Top'}


@mobile_template('landings/{mobile/}home.html')
def home(request, template=None):
    docs = HOME_DOCS_FOR_MOBILE if request.MOBILE else HOME_DOCS
    return jingo.render(request, template, _data(docs, request.locale))


@mobile_template('landings/{mobile/}mobile.html')
def mobile(request, template=None):
    docs = MOBILE_DOCS_FOR_MOBILE if request.MOBILE else MOBILE_DOCS
    data = _data(docs, request.locale)
    data.update(search_params={'q_tags': 'mobile', 'tags': 'mobile'})
    return jingo.render(request, template, data)


@mobile_template('landings/{mobile/}sync.html')
def sync(request, template=None):
    docs = SYNC_DOCS_FOR_MOBILE if request.MOBILE else SYNC_DOCS
    return jingo.render(request, template, _data(docs, request.locale))


@mobile_template('landings/{mobile/}fxhome.html')
def fxhome(request, template=None):
    docs = FXHOME_DOCS_FOR_MOBILE if request.MOBILE else FXHOME_DOCS
    return jingo.render(request, template, _data(docs, request.locale))


def _data(docs, locale):
    """Add the documents and showfor data to the context data."""
    data = {}
    for side, title in docs.iteritems():
        data[side] = get_object_fallback(Document, title, locale)
    data.update(SHOWFOR_DATA)
    return data
