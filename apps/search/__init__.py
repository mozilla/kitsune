import os

from django.conf import settings

import elasticutils
import oedipus
from tower import ugettext_lazy as _lazy
import waffle


WHERE_WIKI = 1
WHERE_SUPPORT = 2
WHERE_BASIC = WHERE_WIKI | WHERE_SUPPORT
WHERE_DISCUSSION = 4

INTERVAL_NONE = 0
INTERVAL_BEFORE = 1
INTERVAL_AFTER = 2

DATE_LIST = (
    (INTERVAL_NONE, _lazy(u"Don't filter")),
    (INTERVAL_BEFORE, _lazy(u'Before')),
    (INTERVAL_AFTER, _lazy(u'After')),
)

GROUPSORT = (
    ('-@relevance', 'age'),  # default
    '-updated',
    '-created',
    '-replies',
)

# For discussion forums
# Integer values here map to tuples from SORT defined above
SORTBY_FORUMS = (
    (0, _lazy(u'Relevance')),
    (1, _lazy(u'Last post date')),
    (2, _lazy(u'Original post date')),
    (3, _lazy(u'Number of replies')),
)

DISCUSSION_STICKY = 1
DISCUSSION_LOCKED = 2

DISCUSSION_STATUS_LIST = (
    (DISCUSSION_STICKY, _lazy(u'Sticky')),
    (DISCUSSION_LOCKED, _lazy(u'Locked')),
)

# For support questions
TERNARY_OFF = 0
TERNARY_YES = 1
TERNARY_NO = -1

TERNARY_LIST = (
    (TERNARY_OFF, _lazy(u"Don't filter")),
    (TERNARY_YES, _lazy(u'Yes')),
    (TERNARY_NO, _lazy(u'No')),
)

NUMBER_LIST = (
    (INTERVAL_NONE, _lazy(u"Don't filter")),
    (INTERVAL_BEFORE, _lazy(u'Less than')),
    (INTERVAL_AFTER, _lazy(u'More than')),
)

SORT_QUESTIONS = (
    ('-@relevance', 'age'),  # default
    ('updated',),
    ('created',),
    ('replies',)
)

SORTBY_QUESTIONS = (
    (0, _lazy(u'Relevance')),
    (1, _lazy(u'Last answer date')),
    (2, _lazy(u'Question date')),
    (3, _lazy(u'Number of answers')),
)


class SphinxSearcher(oedipus.S):
    @property
    def port(self):
        """Twiddle Sphinx port at runtime based on var set in SphinxTestCase"""
        return (settings.TEST_SPHINX_PORT
                if os.environ.get('DJANGO_ENVIRONMENT') == 'test'
                else settings.SPHINX_PORT)


ExcerptTimeoutError = oedipus.ExcerptTimeoutError
ExcerptSocketError = oedipus.ExcerptSocketError
SearchError = oedipus.SearchError


def searcher(request):
    """Return an ``S`` object for use with either ElasticSearch or Sphinx.

    Which it returns depends on the ``elasticsearch`` waffle flag.

    """
    return (oedipus.SphinxTolerantElastic if
            waffle.flag_is_active(request, 'elasticsearch') else
            SphinxSearcher)
