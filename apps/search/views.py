from datetime import datetime, timedelta
from itertools import chain
import json
import re
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.models import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.http import urlquote
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from access.decorators import permission_required
import jingo
import jinja2
from mobility.decorators import mobile_template
from statsd import statsd
from tower import ugettext as _, ugettext_lazy as _lazy

from search import SearchError, ExcerptTimeoutError, ExcerptSocketError
from search.utils import locale_or_default, clean_excerpt, ComposedList
from forums.models import Thread, discussion_searcher
from questions.models import question_searcher
import search as constants
from search.forms import SearchForm
from search.es_utils import ESTimeoutError, ESMaxRetryError, ESException
from search.tasks import ES_REINDEX_PROGRESS
from sumo.utils import paginate, smart_int
from wiki.models import wiki_searcher
import waffle


EXCERPT_JOINER = _lazy(u'...', 'between search excerpts')


def jsonp_is_valid(func):
    func_regex = re.compile(r'^[a-zA-Z_\$][a-zA-Z0-9_\$]*'
        + r'(\[[a-zA-Z0-9_\$]*\])*(\.[a-zA-Z0-9_\$]+(\[[a-zA-Z0-9_\$]*\])*)*$')
    return func_regex.match(func)


class ObjectDict(object):
    def __init__(self, source_dict):
        self.__dict__.update(source_dict)


def search_with_es(request, template=None):
    """ES-specific search view"""

    engine = 'elastic'

    # Time ES and Sphinx separate. See bug 723930.
    # TODO: Remove this once Sphinx is gone.
    start = time.time()

    # JSON-specific variables
    is_json = (request.GET.get('format') == 'json')
    callback = request.GET.get('callback', '').strip()
    mimetype = 'application/x-javascript' if callback else 'application/json'

    # Search "Expires" header format
    expires_fmt = '%A, %d %B %Y %H:%M:%S GMT'

    # Check callback is valid
    if is_json and callback and not jsonp_is_valid(callback):
        return HttpResponse(
            json.dumps({'error': _('Invalid callback function.')}),
            mimetype=mimetype, status=400)

    language = locale_or_default(request.GET.get('language', request.locale))
    r = request.GET.copy()
    a = request.GET.get('a', '0')

    # Search default values
    try:
        category = (map(int, r.getlist('category')) or
                    settings.SEARCH_DEFAULT_CATEGORIES)
    except ValueError:
        category = settings.SEARCH_DEFAULT_CATEGORIES
    r.setlist('category', category)

    # Basic form
    if a == '0':
        r['w'] = r.get('w', constants.WHERE_BASIC)
    # Advanced form
    if a == '2':
        r['language'] = language
        r['a'] = '1'

    # TODO: Rewrite so SearchForm is unbound initially and we can use `initial`
    # on the form fields.
    if 'include_archived' not in r:
        r['include_archived'] = False

    search_form = SearchForm(r)

    if not search_form.is_valid() or a == '2':
        if is_json:
            return HttpResponse(
                json.dumps({'error': _('Invalid search data.')}),
                mimetype=mimetype,
                status=400)

        t = template if request.MOBILE else 'search/form.html'
        search_ = jingo.render(request, t,
                               {'advanced': a, 'request': request,
                                'search_form': search_form})
        search_['Cache-Control'] = 'max-age=%s' % \
                                   (settings.SEARCH_CACHE_PERIOD * 60)
        search_['Expires'] = (datetime.utcnow() +
                              timedelta(
                                minutes=settings.SEARCH_CACHE_PERIOD)) \
                              .strftime(expires_fmt)
        return search_

    cleaned = search_form.cleaned_data

    page = max(smart_int(request.GET.get('page')), 1)
    offset = (page - 1) * settings.SEARCH_RESULTS_PER_PAGE

    # TODO: This is fishy--why does it have to be coded this way?
    # get language name for display in template
    lang = language.lower()
    if settings.LANGUAGES.get(lang):
        lang_name = settings.LANGUAGES[lang]
    else:
        lang_name = ''

    wiki_s = wiki_searcher(request)
    question_s = question_searcher(request)
    discussion_s = discussion_searcher(request)

    # wiki filters
    # Category filter
    if cleaned['category']:
        wiki_s = wiki_s.filter(category__in=cleaned['category'])

    # Locale filter
    wiki_s = wiki_s.filter(locale=language)

    # Product filter
    products = cleaned['product']
    for p in products:
        wiki_s = wiki_s.filter(tag=p)

    # Tags filter
    tags = [t.strip() for t in cleaned['tags'].split()]
    for t in tags:
        wiki_s = wiki_s.filter(tag=t)

    # Archived bit
    if a == '0' and not cleaned['include_archived']:
        # Default to NO for basic search:
        cleaned['include_archived'] = False
    if not cleaned['include_archived']:
        wiki_s = wiki_s.filter(is_archived=False)
    # End of wiki filters

    # Support questions specific filters
    if cleaned['w'] & constants.WHERE_SUPPORT:

        # Solved is set by default if using basic search
        if a == '0' and not cleaned['has_helpful']:
            cleaned['has_helpful'] = constants.TERNARY_YES

        # These filters are ternary, they can be either YES, NO, or OFF
        ternary_filters = ('is_locked', 'is_solved', 'has_answers',
                           'has_helpful')
        d = dict((filter_name, _ternary_filter(cleaned[filter_name]))
                 for filter_name in ternary_filters
                 if cleaned[filter_name])
        if d:
            question_s = question_s.filter(**d)

        if cleaned['asked_by']:
            question_s = question_s.filter(
                question_creator=cleaned['asked_by'])

        if cleaned['answered_by']:
            question_s = question_s.filter(
                answer_creator=cleaned['answered_by'])

        q_tags = [t.strip() for t in cleaned['q_tags'].split()]
        for t in q_tags:
            question_s = question_s.filter(tag=t)

    # Discussion forum specific filters
    if cleaned['w'] & constants.WHERE_DISCUSSION:
        if cleaned['author']:
            discussion_s = discussion_s.filter(author_ord=cleaned['author'])

        if cleaned['thread_type']:
            if constants.DISCUSSION_STICKY in cleaned['thread_type']:
                discussion_s = discussion_s.filter(is_sticky=1)

            if constants.DISCUSSION_LOCKED in cleaned['thread_type']:
                discussion_s = discussion_s.filter(is_locked=1)

        if cleaned['forum']:
            discussion_s = discussion_s.filter(forum_id__in=cleaned['forum'])

    # Filters common to support and discussion forums
    # Created filter
    unix_now = int(time.time())
    interval_filters = (
        ('created', cleaned['created'], cleaned['created_date']),
        ('updated', cleaned['updated'], cleaned['updated_date']),
        ('num_votes', cleaned['num_voted'], cleaned['num_votes']))
    for filter_name, filter_option, filter_date in interval_filters:
        if filter_option == constants.INTERVAL_BEFORE:
            before = {filter_name + '__gte': 0,
                      filter_name + '__lte': max(filter_date, 0)}

            if filter_name != 'num_votes':
                discussion_s = discussion_s.filter(**before)
            question_s = question_s.filter(**before)
        elif filter_option == constants.INTERVAL_AFTER:
            after = {filter_name + '__gte': min(filter_date, unix_now),
                     filter_name + '__lte': unix_now}

            if filter_name != 'num_votes':
                discussion_s = discussion_s.filter(**after)
            question_s = question_s.filter(**after)

    documents = ComposedList()

    sortby = smart_int(request.GET.get('sortby'))
    try:
        max_results = settings.SEARCH_MAX_RESULTS
        cleaned_q = cleaned['q']

        if cleaned['w'] & constants.WHERE_WIKI:
            if cleaned_q:
                wiki_s = wiki_s.query(cleaned_q)
            documents.set_count(('wiki', wiki_s),
                                min(wiki_s.count(), max_results))

        if cleaned['w'] & constants.WHERE_SUPPORT:
            # Sort results by
            try:
                question_s = question_s.order_by(
                    *constants.SORT_QUESTIONS[sortby])
            except IndexError:
                pass

            question_s = question_s.highlight(
                'title', 'question_content', 'answer_content',
                before_match='<b>',
                after_match='</b>',
                limit=settings.SEARCH_SUMMARY_LENGTH)

            if cleaned_q:
                question_s = question_s.query(cleaned_q)
            documents.set_count(('question', question_s),
                                min(question_s.count(), max_results))

        if cleaned['w'] & constants.WHERE_DISCUSSION:
            discussion_s = discussion_s.highlight(
                'content',
                before_match='<b>',
                after_match='</b>',
                limit=settings.SEARCH_SUMMARY_LENGTH)

            if cleaned_q:
                discussion_s = discussion_s.query(cleaned_q)
            documents.set_count(('forum', discussion_s),
                                min(discussion_s.count(), max_results))

        results_per_page = settings.SEARCH_RESULTS_PER_PAGE
        pages = paginate(request, documents, results_per_page)

        # Get the documents we want to show and add them to
        # docs_for_page.
        documents = documents[offset:offset + results_per_page]
        docs_for_page = []
        for (kind, search_s), bounds in documents:
            search_s = search_s.values_dict()[bounds[0]:bounds[1]]
            docs_for_page += [(kind, doc) for doc in search_s]

        results = []
        for i, docinfo in enumerate(docs_for_page):
            rank = i + offset
            # Type here is 'wiki', ... while doc here is an ES result
            # document.
            type_, doc = docinfo

            if type_ == 'wiki':
                summary = doc['summary']
                result = {
                    'url': doc['url'],
                    'title': doc['title'],
                    'type': 'document',
                    'object': ObjectDict(doc)}
            elif type_ == 'question':
                summary = _build_es_excerpt(doc)
                result = {
                    'url': doc['url'],
                    'title': doc['title'],
                    'type': 'question',
                    'object': ObjectDict(doc)}
            else:
                summary = _build_es_excerpt(doc)
                result = {
                    'url': doc['url'],
                    'title': doc['title'],
                    'type': 'thread',
                    'object': ObjectDict(doc)}
            result['search_summary'] = summary
            result['rank'] = rank
            results.append(result)

    except (ESTimeoutError, ESMaxRetryError, ESException), exc:
        # Handle timeout and all those other transient errors with a
        # "Search Unavailable" rather than a Django error page.
        if is_json:
            return HttpResponse(json.dumps({'error':
                                             _('Search Unavailable')}),
                                mimetype=mimetype, status=503)

        if isinstance(exc, ESTimeoutError):
            statsd.incr('search.%s.timeouterror' % engine)
        elif isinstance(exc, ESMaxRetryError):
            statsd.incr('search.%s.maxretryerror' % engine)
        elif isinstance(exc, ESException):
            statsd.incr('search.%s.elasticsearchexception' % engine)

        t = 'search/mobile/down.html' if request.MOBILE else 'search/down.html'
        return jingo.render(request, t, {'q': cleaned['q']}, status=503)

    items = [(k, v) for k in search_form.fields for
             v in r.getlist(k) if v and k != 'a']
    items.append(('a', '2'))

    if is_json:
        # Models are not json serializable.
        for r in results:
            del r['object']
        data = {}
        data['results'] = results
        data['total'] = len(results)
        data['query'] = cleaned['q']
        if not results:
            data['message'] = _('No pages matched the search criteria')
        json_data = json.dumps(data)
        if callback:
            json_data = callback + '(' + json_data + ');'

        return HttpResponse(json_data, mimetype=mimetype)

    results_ = jingo.render(request, template,
        {'num_results': len(documents), 'results': results, 'q': cleaned['q'],
         'pages': pages, 'w': cleaned['w'],
         'search_form': search_form, 'lang_name': lang_name, })
    results_['Cache-Control'] = 'max-age=%s' % \
                                (settings.SEARCH_CACHE_PERIOD * 60)
    results_['Expires'] = (datetime.utcnow() +
                           timedelta(minutes=settings.SEARCH_CACHE_PERIOD)) \
                           .strftime(expires_fmt)
    results_.set_cookie(settings.LAST_SEARCH_COOKIE, urlquote(cleaned['q']),
                        max_age=3600, secure=False, httponly=False)

    # Send timing information for each engine. Bug 723930.
    # TODO: Remove this once Sphinx is gone.
    dt = (time.time() - start) * 1000
    statsd.timing('search.%s.view' % engine, int(dt))

    return results_


def search_with_sphinx(request, template=None):
    """Sphinx-specific search view"""

    # Time ES and Sphinx separate. See bug 723930.
    # TODO: Remove this once Sphinx is gone.
    start = time.time()

    # JSON-specific variables
    is_json = (request.GET.get('format') == 'json')
    callback = request.GET.get('callback', '').strip()
    mimetype = 'application/x-javascript' if callback else 'application/json'

    if waffle.flag_is_active(request, 'elasticsearch'):
        engine = 'elastic'
    else:
        engine = 'sphinx'

    # Search "Expires" header format
    expires_fmt = '%A, %d %B %Y %H:%M:%S GMT'

    # Check callback is valid
    if is_json and callback and not jsonp_is_valid(callback):
        return HttpResponse(
            json.dumps({'error': _('Invalid callback function.')}),
            mimetype=mimetype, status=400)

    language = locale_or_default(request.GET.get('language', request.locale))
    r = request.GET.copy()
    a = request.GET.get('a', '0')

    # Search default values
    try:
        category = map(int, r.getlist('category')) or \
                   settings.SEARCH_DEFAULT_CATEGORIES
    except ValueError:
        category = settings.SEARCH_DEFAULT_CATEGORIES
    r.setlist('category', category)

    # Basic form
    if a == '0':
        r['w'] = r.get('w', constants.WHERE_BASIC)
    # Advanced form
    if a == '2':
        r['language'] = language
        r['a'] = '1'

    # TODO: Rewrite so SearchForm is unbound initially and we can use `initial`
    # on the form fields.
    if 'include_archived' not in r:
        r['include_archived'] = False

    search_form = SearchForm(r)

    if not search_form.is_valid() or a == '2':
        if is_json:
            return HttpResponse(
                json.dumps({'error': _('Invalid search data.')}),
                mimetype=mimetype,
                status=400)

        t = template if request.MOBILE else 'search/form.html'
        search_ = jingo.render(request, t,
                               {'advanced': a, 'request': request,
                                'search_form': search_form})
        search_['Cache-Control'] = 'max-age=%s' % \
                                   (settings.SEARCH_CACHE_PERIOD * 60)
        search_['Expires'] = (datetime.utcnow() +
                              timedelta(
                                minutes=settings.SEARCH_CACHE_PERIOD)) \
                              .strftime(expires_fmt)
        return search_

    cleaned = search_form.cleaned_data

    page = max(smart_int(request.GET.get('page')), 1)
    offset = (page - 1) * settings.SEARCH_RESULTS_PER_PAGE

    # get language name for display in template
    lang = language.lower()
    if settings.LANGUAGES.get(lang):
        lang_name = settings.LANGUAGES[lang]
    else:
        lang_name = ''

    wiki_s = wiki_searcher(request)
    question_s = question_searcher(request)
    discussion_s = discussion_searcher(request)

    documents = []

    # wiki filters
    # Category filter
    if cleaned['category']:
        wiki_s = wiki_s.filter(category__in=cleaned['category'])

    # Locale filter
    wiki_s = wiki_s.filter(locale=language)

    # Product filter
    products = cleaned['product']
    for p in products:
        wiki_s = wiki_s.filter(tag=p)

    # Tags filter
    tags = [t.strip() for t in cleaned['tags'].split()]
    for t in tags:
        wiki_s = wiki_s.filter(tag=t)

    # Archived bit
    if a == '0' and not cleaned['include_archived']:
        # Default to NO for basic search:
        cleaned['include_archived'] = False
    if not cleaned['include_archived']:
        wiki_s = wiki_s.filter(is_archived=False)
    # End of wiki filters

    # Support questions specific filters
    if cleaned['w'] & constants.WHERE_SUPPORT:

        # Solved is set by default if using basic search
        if a == '0' and not cleaned['has_helpful']:
            cleaned['has_helpful'] = constants.TERNARY_YES

        # These filters are ternary, they can be either YES, NO, or OFF
        ternary_filters = ('is_locked', 'is_solved', 'has_answers',
                           'has_helpful')
        d = dict((filter_name, _ternary_filter(cleaned[filter_name]))
                 for filter_name in ternary_filters
                 if cleaned[filter_name])
        if d:
            question_s = question_s.filter(**d)

        if cleaned['asked_by']:
            question_s = question_s.filter(
                question_creator=cleaned['asked_by'])

        if cleaned['answered_by']:
            question_s = question_s.filter(
                answer_creator=cleaned['answered_by'])

        q_tags = [t.strip() for t in cleaned['q_tags'].split()]
        for t in q_tags:
            question_s = question_s.filter(tag=t)

    # Discussion forum specific filters
    if cleaned['w'] & constants.WHERE_DISCUSSION:
        if cleaned['author']:
            discussion_s = discussion_s.filter(author_ord=cleaned['author'])

        if cleaned['thread_type']:
            if constants.DISCUSSION_STICKY in cleaned['thread_type']:
                discussion_s = discussion_s.filter(is_sticky=1)

            if constants.DISCUSSION_LOCKED in cleaned['thread_type']:
                discussion_s = discussion_s.filter(is_locked=1)

        if cleaned['forum']:
            discussion_s = discussion_s.filter(forum_id__in=cleaned['forum'])

    # Filters common to support and discussion forums
    # Created filter
    unix_now = int(time.time())
    interval_filters = (
        ('created', cleaned['created'], cleaned['created_date']),
        ('updated', cleaned['updated'], cleaned['updated_date']),
        ('question_votes', cleaned['num_voted'], cleaned['num_votes']))
    for filter_name, filter_option, filter_date in interval_filters:
        if filter_option == constants.INTERVAL_BEFORE:
            before = {filter_name + '__gte': 0,
                      filter_name + '__lte': max(filter_date, 0)}

            if filter_name != 'question_votes':
                discussion_s = discussion_s.filter(**before)
            question_s = question_s.filter(**before)
        elif filter_option == constants.INTERVAL_AFTER:
            after = {filter_name + '__gte': min(filter_date, unix_now),
                     filter_name + '__lte': unix_now}

            if filter_name != 'question_votes':
                discussion_s = discussion_s.filter(**after)
            question_s = question_s.filter(**after)

    sortby = smart_int(request.GET.get('sortby'))
    try:
        max_results = settings.SEARCH_MAX_RESULTS
        cleaned_q = cleaned['q']

        if cleaned['w'] & constants.WHERE_WIKI:
            if cleaned_q:
                wiki_s = wiki_s.query(cleaned_q)
            wiki_s = wiki_s[:max_results]
            # Execute the query and append to documents
            documents += [('wiki', (pair[0], pair[1]))
                          for pair in enumerate(wiki_s.object_ids())]

        if cleaned['w'] & constants.WHERE_SUPPORT:
            # Sort results by
            try:
                question_s = question_s.order_by(
                    *constants.SORT_QUESTIONS[sortby])
            except IndexError:
                pass

            if engine == 'elastic':
                highlight_fields = ['title', 'question_content',
                                    'answer_content']
            else:
                highlight_fields = ['content']

            question_s = question_s.highlight(
                *highlight_fields,
                before_match='<b>',
                after_match='</b>',
                limit=settings.SEARCH_SUMMARY_LENGTH)

            if cleaned_q:
                question_s = question_s.query(cleaned_q)
            question_s = question_s[:max_results]
            documents += [('question', (pair[0], pair[1]))
                          for pair in enumerate(question_s.object_ids())]

        if cleaned['w'] & constants.WHERE_DISCUSSION:
            # Sort results by
            try:
                # Note that the first attribute needs to be the same
                # here and in forums/models.py discussion_search.
                discussion_s = discussion_s.group_by(
                    'thread_id', constants.GROUPSORT[sortby])
            except IndexError:
                pass

            discussion_s = discussion_s.highlight(
                'content',
                before_match='<b>',
                after_match='</b>',
                limit=settings.SEARCH_SUMMARY_LENGTH)

            if cleaned_q:
                discussion_s = discussion_s.query(cleaned_q)
            discussion_s = discussion_s[:max_results]
            documents += [('discussion', (pair[0], pair[1]))
                          for pair in enumerate(discussion_s.object_ids())]

        pages = paginate(request, documents, settings.SEARCH_RESULTS_PER_PAGE)

        # Build a dict of { type_ -> list of indexes } for the specific
        # docs that we're going to display on this page.  This makes it
        # easy for us to slice the appropriate search Ss so we're limiting
        # our db hits to just the items we're showing.
        documents_dict = {}
        for doc in documents[offset:offset + settings.SEARCH_RESULTS_PER_PAGE]:
            documents_dict.setdefault(doc[0], []).append(doc[1][0])

        docs_for_page = []
        for kind, search_s in [('wiki', wiki_s),
                                ('question', question_s),
                                ('discussion', discussion_s)]:
            if kind not in documents_dict:
                continue

            # documents_dict[type_] is a list of indexes--one for each
            # object id search result for that type_.  We use the values
            # at the beginning and end of the list for slice boundaries.
            begin = documents_dict[kind][0]
            end = documents_dict[kind][-1] + 1

            search_s = search_s[begin:end]

            if engine == 'elastic':
                # If we're doing elasticsearch, then we need to update
                # the _s variables to point to the sliced versions of
                # S so that, when we iterate over them in the
                # following list comp, we hang onto the version that
                # does the query, so we can call excerpt() on it
                # later.
                #
                # We only need to do this with elasticsearch.  For Sphinx,
                # search_s at this point is an ObjectResults and not an S
                # because we've already acquired object_ids on it.  Thus
                # if we update the _s variables, we'd be pointing to the
                # ObjectResults and not the S and then excerpting breaks.
                #
                # Ugh.
                if kind == 'wiki':
                    wiki_s = search_s
                elif kind == 'question':
                    question_s = search_s
                elif kind == 'discussion':
                    discussion_s = search_s

            docs_for_page += [(kind, doc) for doc in search_s]

        results = []
        for i, docinfo in enumerate(docs_for_page):
            rank = i + offset
            type_, doc = docinfo
            try:
                if type_ == 'wiki':
                    summary = doc.current_revision.summary
                    result = {
                        'url': doc.get_absolute_url(),
                        'title': doc.title,
                        'type': 'document',
                        'object': doc}
                elif type_ == 'question':
                    summary = _build_excerpt(question_s, doc)
                    result = {
                        'url': doc.get_absolute_url(),
                        'title': doc.title,
                        'type': 'question',
                        'object': doc}
                else:
                    if engine == 'elastic':
                        thread = doc
                    else:
                        thread = Thread.objects.get(pk=doc.thread_id)

                    summary = _build_excerpt(discussion_s, doc)
                    result = {
                        'url': thread.get_absolute_url(),
                        'title': thread.title,
                        'type': 'thread',
                        'object': thread}
                result['search_summary'] = summary
                result['rank'] = rank
                results.append(result)
            except IndexError:
                break
            except ObjectDoesNotExist:
                continue

    except (SearchError, ESTimeoutError, ESMaxRetryError, ESException), exc:
        # Handle timeout and all those other transient errors with a
        # "Search Unavailable" rather than a Django error page.
        if is_json:
            return HttpResponse(json.dumps({'error':
                                             _('Search Unavailable')}),
                                mimetype=mimetype, status=503)

        if isinstance(exc, SearchError):
            statsd.incr('search.%s.searcherror' % engine)
        elif isinstance(exc, ESTimeoutError):
            statsd.incr('search.%s.timeouterror' % engine)
        elif isinstance(exc, ESMaxRetryError):
            statsd.incr('search.%s.maxretryerror' % engine)
        elif isinstance(exc, ESException):
            statsd.incr('search.%s.elasticsearchexception' % engine)

        t = 'search/mobile/down.html' if request.MOBILE else 'search/down.html'
        return jingo.render(request, t, {'q': cleaned['q']}, status=503)

    items = [(k, v) for k in search_form.fields for
             v in r.getlist(k) if v and k != 'a']
    items.append(('a', '2'))

    if is_json:
        # Models are not json serializable.
        for r in results:
            del r['object']
        data = {}
        data['results'] = results
        data['total'] = len(results)
        data['query'] = cleaned['q']
        if not results:
            data['message'] = _('No pages matched the search criteria')
        json_data = json.dumps(data)
        if callback:
            json_data = callback + '(' + json_data + ');'

        return HttpResponse(json_data, mimetype=mimetype)

    results_ = jingo.render(request, template,
        {'num_results': len(documents), 'results': results, 'q': cleaned['q'],
         'pages': pages, 'w': cleaned['w'],
         'search_form': search_form, 'lang_name': lang_name, })
    results_['Cache-Control'] = 'max-age=%s' % \
                                (settings.SEARCH_CACHE_PERIOD * 60)
    results_['Expires'] = (datetime.utcnow() +
                           timedelta(minutes=settings.SEARCH_CACHE_PERIOD)) \
                           .strftime(expires_fmt)
    results_.set_cookie(settings.LAST_SEARCH_COOKIE, urlquote(cleaned['q']),
                        max_age=3600, secure=False, httponly=False)

    # Send timing information for each engine. Bug 723930.
    # TODO: Remove this once Sphinx is gone.
    dt = (time.time() - start) * 1000
    statsd.timing('search.%s.view' % engine, int(dt))

    return results_


@mobile_template('search/{mobile/}results.html')
def search(request, template=None):
    """Performs search or displays the search form."""

    # This is a complete split of the Sphinx from ES code with little
    # to no code sharing.
    #
    # While this makes it harder to make changes to both the ES and
    # Sphinx sides and also possibly makes it testing more difficult,
    # it simplifies making big changes to the ES side and we'll have
    # to do very little work to ditch Sphinx altogether in the near
    # future.

    if waffle.flag_is_active(request, 'elasticsearch'):
        return search_with_es(request, template)
    else:
        return search_with_sphinx(request, template)


@cache_page(60 * 15)  # 15 minutes.
def suggestions(request):
    """A simple search view that returns OpenSearch suggestions."""
    mimetype = 'application/x-suggestions+json'

    term = request.GET.get('q')
    if not term:
        return HttpResponseBadRequest(mimetype=mimetype)

    site = Site.objects.get_current()
    locale = locale_or_default(request.locale)
    results = list(chain(
            wiki_searcher(request).filter(is_archived=False)
                                  .filter(locale=locale)
                                  .query(term)[:5],
            question_searcher(request).filter(has_helpful=True)
                                      .query(term)[:5]))
    # Assumption: wiki_search sets filter(is_archived=False).

    urlize = lambda obj: u'https://%s%s' % (site, obj.get_absolute_url())
    data = [term, [r.title for r in results], [], [urlize(r) for r in results]]
    return HttpResponse(json.dumps(data), mimetype=mimetype)


@cache_page(60 * 60 * 168)  # 1 week.
def plugin(request):
    """Render an OpenSearch Plugin."""
    site = Site.objects.get_current()
    return jingo.render(request, 'search/plugin.html',
                        {'site': site, 'locale': request.locale},
                        mimetype='application/opensearchdescription+xml')


@require_GET
@permission_required('search.reindex')
def reindex_progress(request):
    """If a reindex is in progress, return its ratio of completeness as text.

    If not, return ''.

    """
    return HttpResponse(cache.get(ES_REINDEX_PROGRESS, ''),
                        mimetype='text/plain')


def _ternary_filter(ternary_value):
    """Return a search query given a TERNARY_YES or TERNARY_NO.

    Behavior for TERNARY_OFF is undefined.

    """
    return ternary_value == constants.TERNARY_YES


def _build_excerpt(searcher, model_obj):
    """Return concatenated search excerpts for Sphinx.

    :arg searcher: The ``S`` object that did the search
    :arg model_obj: The model object returned by the search

    """
    try:
        excerpt = EXCERPT_JOINER.join(
            [m.strip() for m in
             chain(*searcher.excerpt(model_obj)) if m])
    except ExcerptTimeoutError:
        statsd.incr('search.excerpt.timeout')
        excerpt = u''
    except ExcerptSocketError:
        statsd.incr('search.excerpt.socketerror')
        excerpt = u''

    return jinja2.Markup(clean_excerpt(excerpt))


def _build_es_excerpt(result):
    """Return concatenated search excerpts.

    :arg result: The result object from the queryset results

    """
    excerpt = EXCERPT_JOINER.join(
        [m.strip() for m in
         chain(*result.highlighted.values()) if m])

    return jinja2.Markup(clean_excerpt(excerpt))
