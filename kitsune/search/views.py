import json
import re
import time
from datetime import datetime, timedelta
from itertools import chain

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.utils.html import escape
from django.utils.http import urlquote
from django.views.decorators.cache import cache_page

import bleach
import jinja2
from elasticutils.utils import format_explanation
from mobility.decorators import mobile_template
from statsd import statsd
from tower import ugettext as _, ugettext_lazy as _lazy

from kitsune import search as constants
from kitsune.forums.models import Forum, ThreadMappingType
from kitsune.products.models import Product
from kitsune.questions.models import QuestionMappingType
from kitsune.search.models import get_mapping_types
from kitsune.search.utils import locale_or_default, clean_excerpt, ComposedList
from kitsune.search import es_utils
from kitsune.search.forms import SearchForm
from kitsune.search.es_utils import ES_EXCEPTIONS, F, AnalyzerS
from kitsune.sumo.utils import paginate, smart_int
from kitsune.wiki.facets import documents_for
from kitsune.wiki.models import DocumentMappingType


EXCERPT_JOINER = _lazy(u'...', 'between search excerpts')


def jsonp_is_valid(func):
    func_regex = re.compile(r'^[a-zA-Z_\$][a-zA-Z0-9_\$]*'
        + r'(\[[a-zA-Z0-9_\$]*\])*(\.[a-zA-Z0-9_\$]+(\[[a-zA-Z0-9_\$]*\])*)*$')
    return func_regex.match(func)


class ObjectDict(object):
    def __init__(self, source_dict):
        self.__dict__.update(source_dict)


@mobile_template('search/{mobile/}results.html')
def search(request, template=None):
    """ES-specific search view"""

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

    language = locale_or_default(
        request.GET.get('language', request.LANGUAGE_CODE))
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

    # TODO: Rewrite so SearchForm is unbound initially and we can use
    # `initial` on the form fields.
    if 'include_archived' not in r:
        r['include_archived'] = False

    search_form = SearchForm(r)
    search_form.set_allowed_forums(request.user)

    if not search_form.is_valid() or a == '2':
        if is_json:
            return HttpResponse(
                json.dumps({'error': _('Invalid search data.')}),
                mimetype=mimetype,
                status=400)

        t = template if request.MOBILE else 'search/form.html'
        search_ = render(request, t, {
            'advanced': a, 'request': request,
            'search_form': search_form})
        search_['Cache-Control'] = 'max-age=%s' % \
                                   (settings.SEARCH_CACHE_PERIOD * 60)
        search_['Expires'] = (datetime.utcnow() +
                              timedelta(
                                minutes=settings.SEARCH_CACHE_PERIOD)) \
                              .strftime(expires_fmt)
        return search_

    cleaned = search_form.cleaned_data

    if request.MOBILE and cleaned['w'] == constants.WHERE_BASIC:
        cleaned['w'] = constants.WHERE_WIKI

    page = max(smart_int(request.GET.get('page')), 1)
    offset = (page - 1) * settings.SEARCH_RESULTS_PER_PAGE

    lang = language.lower()
    if settings.LANGUAGES.get(lang):
        lang_name = settings.LANGUAGES[lang]
    else:
        lang_name = ''

    # We use a regular S here because we want to search across
    # multiple doctypes.
    searcher = (AnalyzerS().es(urls=settings.ES_URLS)
                .indexes(es_utils.read_index('default')))

    wiki_f = F(model='wiki_document')
    question_f = F(model='questions_question')
    discussion_f = F(model='forums_thread')

    # Start - wiki filters

    if cleaned['w'] & constants.WHERE_WIKI:
        # Category filter
        if cleaned['category']:
            wiki_f &= F(document_category__in=cleaned['category'])

        # Locale filter
        wiki_f &= F(document_locale=language)

        # Product filter
        products = cleaned['product']
        for p in products:
            wiki_f &= F(product=p)

        # Topics filter
        topics = cleaned['topics']
        for t in topics:
            wiki_f &= F(topic=t)

        # Archived bit
        if a == '0' and not cleaned['include_archived']:
            # Default to NO for basic search:
            cleaned['include_archived'] = False
        if not cleaned['include_archived']:
            wiki_f &= F(document_is_archived=False)

    # End - wiki filters

    # Start - support questions filters

    if cleaned['w'] & constants.WHERE_SUPPORT:
        # Solved is set by default if using basic search
        if a == '0' and not cleaned['has_helpful']:
            cleaned['has_helpful'] = constants.TERNARY_YES

        # These filters are ternary, they can be either YES, NO, or OFF
        ternary_filters = ('is_locked', 'is_solved', 'has_answers',
                           'has_helpful', 'is_archived')
        d = dict(('question_%s' % filter_name,
                  _ternary_filter(cleaned[filter_name]))
                 for filter_name in ternary_filters if cleaned[filter_name])
        if d:
            question_f &= F(**d)

        if cleaned['asked_by']:
            question_f &= F(question_creator=cleaned['asked_by'])

        if cleaned['answered_by']:
            question_f &= F(question_answer_creator=cleaned['answered_by'])

        q_tags = [t.strip() for t in cleaned['q_tags'].split(',')]
        for t in q_tags:
            if t:
                question_f &= F(question_tag=t)

        # Product filter
        products = cleaned['product']
        for p in products:
            question_f &= F(product=p)

        # Topics filter
        topics = cleaned['topics']
        for t in topics:
            question_f &= F(topic=t)

    # End - support questions filters

    # Start - discussion forum filters

    if cleaned['w'] & constants.WHERE_DISCUSSION:
        if cleaned['author']:
            discussion_f &= F(post_author_ord=cleaned['author'])

        if cleaned['thread_type']:
            if constants.DISCUSSION_STICKY in cleaned['thread_type']:
                discussion_f &= F(post_is_sticky=1)

            if constants.DISCUSSION_LOCKED in cleaned['thread_type']:
                discussion_f &= F(post_is_locked=1)

        valid_forum_ids = [
            f.id for f in Forum.authorized_forums_for_user(request.user)]

        forum_ids = None
        if cleaned['forum']:
            forum_ids = [f for f in cleaned['forum'] if f in valid_forum_ids]

        # If we removed all the forums they wanted to look at or if
        # they didn't specify, then we filter on the list of all
        # forums they're authorized to look at.
        if not forum_ids:
            forum_ids = valid_forum_ids

        discussion_f &= F(post_forum_id__in=forum_ids)

    # End - discussion forum filters

    # Created filter
    unix_now = int(time.time())
    interval_filters = (
        ('created', cleaned['created'], cleaned['created_date']),
        ('updated', cleaned['updated'], cleaned['updated_date']))
    for filter_name, filter_option, filter_date in interval_filters:
        if filter_option == constants.INTERVAL_BEFORE:
            before = {filter_name + '__gte': 0,
                      filter_name + '__lte': max(filter_date, 0)}

            discussion_f &= F(**before)
            question_f &= F(**before)
        elif filter_option == constants.INTERVAL_AFTER:
            after = {filter_name + '__gte': min(filter_date, unix_now),
                     filter_name + '__lte': unix_now}

            discussion_f &= F(**after)
            question_f &= F(**after)

    # In basic search, we limit questions from the last
    # SEARCH_DEFAULT_MAX_QUESTION_AGE seconds.
    if a == '0':
        start_date = unix_now - settings.SEARCH_DEFAULT_MAX_QUESTION_AGE
        question_f &= F(created__gte=start_date)

    # Note: num_voted (with a d) is a different field than num_votes
    # (with an s). The former is a dropdown and the latter is an
    # integer value.
    if cleaned['num_voted'] == constants.INTERVAL_BEFORE:
        question_f &= F(question_num_votes__lte=max(cleaned['num_votes'], 0))
    elif cleaned['num_voted'] == constants.INTERVAL_AFTER:
        question_f &= F(question_num_votes__gte=cleaned['num_votes'])

    # Done with all the filtery stuff--time  to generate results

    # Combine all the filters and add to the searcher
    doctypes = []
    final_filter = F()
    if cleaned['w'] & constants.WHERE_WIKI:
        doctypes.append(DocumentMappingType.get_mapping_type_name())
        final_filter |= wiki_f

    if cleaned['w'] & constants.WHERE_SUPPORT:
        doctypes.append(QuestionMappingType.get_mapping_type_name())
        final_filter |= question_f

    if cleaned['w'] & constants.WHERE_DISCUSSION:
        doctypes.append(ThreadMappingType.get_mapping_type_name())
        final_filter |= discussion_f

    searcher = searcher.doctypes(*doctypes)
    searcher = searcher.filter(final_filter)

    if 'explain' in request.GET and request.GET['explain'] == '1':
        searcher = searcher.explain()

    documents = ComposedList()

    try:
        cleaned_q = cleaned['q']

        # Set up the highlights. Show the entire field highlighted.
        searcher = searcher.highlight(
            'question_content',  # support forum
            'document_summary',  # kb
            'post_content',  # contributor forum
            pre_tags=['<b>'],
            post_tags=['</b>'],
            number_of_fragments=0)

        # Set up boosts
        searcher = searcher.boost(
            question_title=4.0,
            question_content=3.0,
            question_answer_content=3.0,
            post_title=2.0,
            post_content=1.0,
            document_title=6.0,
            document_content=1.0,
            document_keywords=8.0,
            document_summary=2.0,

            # Text phrases in document titles and content get an extra
            # boost.
            document_title__text_phrase=10.0,
            document_content__text_phrase=8.0)

        # Apply sortby for advanced search of questions
        if cleaned['w'] == constants.WHERE_SUPPORT:
            sortby = cleaned['sortby']
            try:
                searcher = searcher.order_by(
                    *constants.SORT_QUESTIONS[sortby])
            except IndexError:
                # Skip index errors because they imply the user is
                # sending us sortby values that aren't valid.
                pass

        # Apply sortby for advanced search of kb documents
        if cleaned['w'] == constants.WHERE_WIKI:
            sortby = cleaned['sortby_documents']
            try:
                searcher = searcher.order_by(
                    *constants.SORT_DOCUMENTS[sortby])
            except IndexError:
                # Skip index errors because they imply the user is
                # sending us sortby values that aren't valid.
                pass

        # Build the query
        if cleaned_q:
            query_fields = chain(*[cls.get_query_fields()
                                   for cls in get_mapping_types()])
            query = {}
            # Create text and text_phrase queries for every field
            # we want to search.
            for field in query_fields:
                for query_type in ['text', 'text_phrase']:
                    query['%s__%s' % (field, query_type)] = cleaned_q

            # Transform the query to use locale aware analyzers.
            query = es_utils.es_query_with_analyzer(query, language)

            searcher = searcher.query(should=True, **query)

        num_results = min(searcher.count(), settings.SEARCH_MAX_RESULTS)

        # TODO - Can ditch the ComposedList here, but we need
        # something that paginate can use to figure out the paging.
        documents = ComposedList()
        documents.set_count(('results', searcher), num_results)

        results_per_page = settings.SEARCH_RESULTS_PER_PAGE
        pages = paginate(request, documents, results_per_page)

        # If we know there aren't any results, let's cheat and in
        # doing that, not hit ES again.
        if num_results == 0:
            searcher = []
        else:
            # Get the documents we want to show and add them to
            # docs_for_page
            documents = documents[offset:offset + results_per_page]

            if len(documents) == 0:
                # If the user requested a page that's beyond the
                # pagination, then documents is an empty list and
                # there are no results to show.
                searcher = []
            else:
                bounds = documents[0][1]
                searcher = searcher.values_dict()[bounds[0]:bounds[1]]

        results = []
        for i, doc in enumerate(searcher):
            rank = i + offset

            if doc['model'] == 'wiki_document':
                summary = _build_es_excerpt(doc)
                if not summary:
                    summary = doc['document_summary']
                result = {
                    'title': doc['document_title'],
                    'type': 'document'}

            elif doc['model'] == 'questions_question':
                summary = _build_es_excerpt(doc)
                if not summary:
                    # We're excerpting only question_content, so if
                    # the query matched question_title or
                    # question_answer_content, then there won't be any
                    # question_content excerpts. In that case, just
                    # show the question--but only the first 500
                    # characters.
                    summary = bleach.clean(
                        doc['question_content'], strip=True)[:500]

                result = {
                    'title': doc['question_title'],
                    'type': 'question',
                    'is_solved': doc['question_is_solved'],
                    'num_answers': doc['question_num_answers'],
                    'num_votes': doc['question_num_votes'],
                    'num_votes_past_week': doc['question_num_votes_past_week']}

            else:
                summary = _build_es_excerpt(doc, first_only=True)
                result = {
                    'title': doc['post_title'],
                    'type': 'thread'}

            result['url'] = doc['url']
            result['object'] = ObjectDict(doc)
            result['search_summary'] = summary
            result['rank'] = rank
            result['score'] = doc._score
            result['explanation'] = escape(format_explanation(
                    doc._explanation))
            results.append(result)

    except ES_EXCEPTIONS as exc:
        # Handle timeout and all those other transient errors with a
        # "Search Unavailable" rather than a Django error page.
        if is_json:
            return HttpResponse(json.dumps({'error':
                                             _('Search Unavailable')}),
                                mimetype=mimetype, status=503)

        # Cheating here: Convert from 'Timeout()' to 'timeout' so
        # we have less code, but still have good stats.
        exc_bucket = repr(exc).lower().strip('()')
        statsd.incr('search.esunified.{0}'.format(exc_bucket))

        import logging
        logging.exception(exc)

        t = 'search/mobile/down.html' if request.MOBILE else 'search/down.html'
        return render(request, t, {'q': cleaned['q']}, status=503)

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

    fallback_results = None
    if num_results == 0:
        fallback_results = _fallback_results(language, cleaned['product'])

    product = Product.objects.filter(slug__in=cleaned['product'])
    if product:
        product_titles = [_(p.title, 'DB: products.Product.title')
                          for p in product]
    else:
        product_titles = [_('All Products')]

    product_titles = ', '.join(product_titles)

    results_ = render(request, template, {
        'num_results': num_results,
        'results': results,
        'fallback_results': fallback_results,
        'q': cleaned['q'],
        'w': cleaned['w'],
        'product': product,
        'products': Product.objects.filter(visible=True),
        'product_titles': product_titles,
        'pages': pages,
        'search_form': search_form,
        'lang_name': lang_name, })
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
    locale = locale_or_default(request.LANGUAGE_CODE)
    try:
        query = dict(('%s__text' % field, term)
                     for field in DocumentMappingType.get_query_fields())
        # Upgrade the query to an analyzer-aware one.
        query = es_utils.es_query_with_analyzer(query, locale)

        wiki_s = (DocumentMappingType.search()
                  .filter(document_is_archived=False)
                  .filter(document_locale=locale)
                  .values_dict('document_title', 'url')
                  .query(or_=query)[:5])

        query = dict(('%s__text' % field, term)
                     for field in QuestionMappingType.get_query_fields())
        question_s = (QuestionMappingType.search()
                      .filter(question_has_helpful=True)
                      .values_dict('question_title', 'url')
                      .query(or_=query)[:5])

        results = list(chain(question_s, wiki_s))
    except ES_EXCEPTIONS:
        # If we have ES problems, we just send back an empty result
        # set.
        results = []

    urlize = lambda r: u'https://%s%s' % (site, r['url'])
    titleize = lambda r: (r['document_title'] if 'document_title' in r
                          else r['question_title'])
    data = [term,
            [titleize(r) for r in results],
            [],
            [urlize(r) for r in results]]
    return HttpResponse(json.dumps(data), mimetype=mimetype)


@cache_page(60 * 60 * 168)  # 1 week.
def plugin(request):
    """Render an OpenSearch Plugin."""
    site = Site.objects.get_current()
    return render(request, 'search/plugin.html', {
        'site': site, 'locale': request.LANGUAGE_CODE},
        content_type='application/opensearchdescription+xml')


def _ternary_filter(ternary_value):
    """Return a search query given a TERNARY_YES or TERNARY_NO.

    Behavior for TERNARY_OFF is undefined.

    """
    return ternary_value == constants.TERNARY_YES


def _build_es_excerpt(result, first_only=False):
    """Return concatenated search excerpts.

    :arg result: The result object from the queryset results
    :arg first_only: True if we should show only the first bit, False
        if we should show all bits

    """
    bits = [m.strip() for m in
            chain(*result._highlight.values()) if m]

    if first_only and bits:
        excerpt = bits[0]
    else:
        excerpt = EXCERPT_JOINER.join(
            [m.strip() for m in
             chain(*result._highlight.values()) if m])

    return jinja2.Markup(clean_excerpt(excerpt))


def _fallback_results(locale, product_slugs):
    """Return the top 20 articles by votes for the given product(s)."""
    products = []
    for slug in product_slugs:
        try:
            p = Product.objects.get(slug=slug)
            products.append(p)
        except Product.DoesNotExist:
            pass

    docs, fallback = documents_for(locale, products=products)
    docs = docs + (fallback or [])

    return docs[:20]
