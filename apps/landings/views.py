import jingo
from mobility.decorators import mobile_template
from tower import ugettext_lazy as _lazy

from sumo.parser import get_object_fallback
from wiki.models import Document
from wiki.views import SHOWFOR_DATA


HOME_DOCS = {'quick': 'Home page - Quick', 'explore': 'Home page - Explore'}
MOBILE_DOCS = {'quick': 'Mobile home - Quick',
               'explore': 'Mobile home - Explore'}
SYNC_DOCS = {'quick': 'Sync home - Quick', 'explore': 'Sync home - Explore'}
FXHOME_DOCS = {'quick': 'FxHome home - Quick',
              'explore': 'FxHome home - Explore'}
HOME_DOCS_FOR_MOBILE = {'common':
                        'Desktop home for mobile - Common Questions'}
MOBILE_DOCS_FOR_MOBILE = {'common':
                          'Mobile home for mobile - Common Questions'}
SYNC_DOCS_FOR_MOBILE = {'common':
                        'Sync home for mobile - Common Questions'}
FXHOME_DOCS_FOR_MOBILE = {'common':
                          'FxHome home for mobile - Common Questions'}


@mobile_template('landings/{mobile/}home.html')
def home(request, template=None):
    docs = HOME_DOCS_FOR_MOBILE if request.MOBILE else HOME_DOCS
    return jingo.render(request, template, _data(docs, request.locale))


@mobile_template('landings/{mobile/}mobile.html')
def mobile(request, template=None):
    docs = MOBILE_DOCS_FOR_MOBILE if request.MOBILE else MOBILE_DOCS
    return jingo.render(request, template, _data(docs, request.locale))


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
        message = _lazy(u'The template "%s" does not exist.') % title
        data[side] = get_object_fallback(Document, title, locale, message)
    data.update(SHOWFOR_DATA)
    return data
