import jingo
from mobility.decorators import mobile_template
from tower import ugettext_lazy as _lazy

from sumo.parser import get_object_fallback
from wiki.models import Document
from wiki.views import SHOWFOR_DATA


HOME_DOCS = {'quick': 'Home page - Quick', 'explore': 'Home page - Explore'}
MOBILE_DOCS = {'quick': 'Mobile home - Quick',
               'explore': 'Mobile home - Explore'}
HOME_DOCS_FOR_MOBILE = {'common':
                        'Desktop home for mobile - Common Questions'}
MOBILE_DOCS_FOR_MOBILE = {'common':
                          'Mobile home for mobile - Common Questions'}


@mobile_template('landings/{mobile/}home.html')
def home(request, template=None):
    data = {}
    docs = HOME_DOCS_FOR_MOBILE if request.MOBILE else HOME_DOCS
    for side, title in docs.iteritems():
        message = _lazy(u'The template "%s" does not exist.') % title
        data[side] = get_object_fallback(
            Document, title, request.locale, message)

    data.update(SHOWFOR_DATA)
    return jingo.render(request, template, data)


@mobile_template('landings/{mobile/}mobile.html')
def mobile(request, template=None):
    data = {}
    docs = MOBILE_DOCS_FOR_MOBILE if request.MOBILE else MOBILE_DOCS
    for side, title in docs.iteritems():
        message = _lazy(u'The template "%s" does not exist.') % title
        data[side] = get_object_fallback(
            Document, title, request.locale, message)

    data.update(SHOWFOR_DATA)
    return jingo.render(request, template, data)
