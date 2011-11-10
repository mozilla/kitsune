from datetime import datetime, timedelta
from itertools import chain
import json
import re
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.http import urlquote
from django.views.decorators.cache import cache_page

import jingo
import jinja2
from mobility.decorators import mobile_template
from statsd import statsd
from tower import ugettext as _

from search import SearchError, ExcerptTimeoutError, ExcerptSocketErrorError
from search.utils import locale_or_default, clean_excerpt
from forums.models import Thread, discussion_search
from questions.models import question_search
import search as constants
from search.forms import SearchForm
from sumo.utils import paginate, smart_int
from wiki.models import wiki_search


def jsonp_is_valid(func):
    func_regex = re.compile(r'^[a-zA-Z_\$][a-zA-Z0-9_\$]*'
        + r'(\[[a-zA-Z0-9_\$]*\])*(\.[a-zA-Z0-9_\$]+(\[[a-zA-Z0-9_\$]*\])*)*$')
    return func_regex.match(func)


@mobile_template('search/{mobile/}results.html')
def search(request, template=None):
    """Performs search or displays the search form."""

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

    wiki_s = wiki_search
    question_s = question_search
    discussion_s = discussion_search

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
            wiki_s = wiki_s.query(cleaned_q)[:max_results]
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

            question_s = question_s.highlight(
                'content',
                before_match='<b>',
                after_match='</b>',
                limit=settings.SEARCH_SUMMARY_LENGTH)

            question_s = question_s.query(cleaned_q)[:max_results]
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

            discussion_s = discussion_s.query(cleaned_q)[:max_results]
            documents += [('discussion', (pair[0], pair[1]))
                          for pair in enumerate(discussion_s.object_ids())]

    except SearchError:
        if is_json:
            return HttpResponse(json.dumps({'error':
                                             _('Search Unavailable')}),
                                mimetype=mimetype, status=503)

        t = 'search/mobile/down.html' if request.MOBILE else 'search/down.html'
        return jingo.render(request, t, {'q': cleaned['q']}, status=503)

    pages = paginate(request, documents, settings.SEARCH_RESULTS_PER_PAGE)

    # Build a dict of { type_ -> list of indexes } for the specific
    # docs that we're going to display on this page.  This makes it
    # easy for us to slice the appropriate search Ss so we're limiting
    # our db hits to just the items we're showing.
    documents_dict = {}
    for doc in documents[offset:offset + settings.SEARCH_RESULTS_PER_PAGE]:
        documents_dict.setdefault(doc[0], []).append(doc[1][0])

    docs_for_page = []
    for type_, search_s in [('wiki', wiki_s),
                            ('question', question_s),
                            ('discussion', discussion_s)]:
        if type_ not in documents_dict:
            continue

        # documents_dict[type_] is a list of indexes--one for each
        # object id search result for that type_.  We use the values
        # at the beginning and end of the list for slice boundaries.
        begin = documents_dict[type_][0]
        end = documents_dict[type_][-1] + 1
        docs_for_page += [(type_, doc) for doc in search_s[begin:end]]

    results = []
    for i, docinfo in enumerate(docs_for_page):
        rank = i + offset
        type_, doc = docinfo
        try:
            if type_ == 'wiki':
                summary = doc.current_revision.summary

                result = {
                    'search_summary': summary,
                    'url': doc.get_absolute_url(),
                    'title': doc.title,
                    'type': 'document',
                    'rank': rank,
                    'object': doc,
                }
                results.append(result)

            elif type_ == 'question':
                try:
                    excerpt = question_s.excerpt(doc)[0]
                except ExcerptTimeoutError:
                    statsd.incr('search.excerpt.timeout')
                    excerpt = u''
                except ExcerptSocketErrorError:
                    statsd.incr('search.excerpt.socketerror')
                    excerpt = u''

                summary = jinja2.Markup(clean_excerpt(excerpt))

                result = {
                    'search_summary': summary,
                    'url': doc.get_absolute_url(),
                    'title': doc.title,
                    'type': 'question',
                    'rank': rank,
                    'object': doc,
                }
                results.append(result)

            else:
                # discussion_s is based on Post--not Thread, so we have
                # to get this manually.
                thread = Thread.objects.get(pk=doc.thread_id)

                try:
                    excerpt = discussion_s.excerpt(doc)[0]
                except ExcerptTimeoutError:
                    statsd.incr('search.excerpt.timeout')
                    excerpt = u''
                except ExcerptSocketErrorError:
                    statsd.incr('search.excerpt.socketerror')
                    excerpt = u''

                summary = jinja2.Markup(clean_excerpt(excerpt))

                result = {
                    'search_summary': summary,
                    'url': thread.get_absolute_url(),
                    'title': thread.title,
                    'type': 'thread',
                    'rank': rank,
                    'object': thread,
                }
                results.append(result)
        except IndexError:
            break
        except ObjectDoesNotExist:
            continue

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
    return results_


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
            wiki_search.filter(is_archived=False)
                       .filter(locale=locale)
                       .query(term)[:5],
            question_search.filter(has_helpful=True).query(term)[:5]))
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


def _ternary_filter(ternary_value):
    """Return a search query given a TERNARY_YES or TERNARY_NO.

    Behavior for TERNARY_OFF is undefined.

    """
    return ternary_value == constants.TERNARY_YES
