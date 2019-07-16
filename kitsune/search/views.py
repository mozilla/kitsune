import json
import logging
import time
from datetime import datetime, timedelta
from itertools import chain

from django.conf import settings
from django.http import (
    HttpResponse, HttpResponseBadRequest, HttpResponseRedirect)
from django.shortcuts import render, render_to_response
from django.utils.html import escape
from django.utils.http import urlquote
from django.utils.translation import ugettext as _, pgettext, pgettext_lazy
from django.views.decorators.cache import cache_page

import bleach
import jinja2
from elasticutils.utils import format_explanation
from elasticutils.contrib.django import ES_EXCEPTIONS
from elasticsearch import RequestsHttpConnection
from kitsune import search as constants
from kitsune.forums.models import Forum, ThreadMappingType
from kitsune.products.models import Product
from kitsune.questions.models import QuestionMappingType
from kitsune.search.utils import locale_or_default, clean_excerpt
from kitsune.search import es_utils
from kitsune.search.forms import SimpleSearchForm, AdvancedSearchForm
from kitsune.search.es_utils import F, AnalyzerS, handle_es_errors
from kitsune.search.search_utils import apply_boosts, generate_simple_search
from kitsune.sumo.api_utils import JSONRenderer
from kitsune.sumo.templatetags.jinja_helpers import Paginator
from kitsune.sumo.json_utils import markup_json
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import paginate
from kitsune.wiki.facets import documents_for
from kitsune.wiki.models import DocumentMappingType


log = logging.getLogger('k.search')


EXCERPT_JOINER = pgettext_lazy('between search excerpts', u'...')


def cache_control(resp, cache_period):
    """Inserts cache/expires headers"""
    resp['Cache-Control'] = 'max-age=%s' % (cache_period * 60)
    resp['Expires'] = (
        (datetime.utcnow() + timedelta(minutes=cache_period))
        .strftime('%A, %d %B %Y %H:%M:%S GMT'))
    return resp


def _es_down_template(request, *args, **kwargs):
    """Returns the appropriate "Elasticsearch is down!" template"""
    return 'search/down.html'


class UnknownDocType(Exception):
    """Signifies a doctype for which there's no handling"""
    pass


def build_results_list(pages, is_json):
    """Takes a paginated search and returns results List

    Handles wiki documents, questions and contributor forum posts.

    :arg pages: paginated S
    :arg is_json: whether or not this is generated results for json output

    :returns: list of dicts

    """
    results = []
    for rank, doc in enumerate(pages, pages.start_index()):
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
                # We're excerpting only question_content, so if the query matched
                # question_title or question_answer_content, then there won't be any
                # question_content excerpts. In that case, just show the question--but
                # only the first 500 characters.
                summary = bleach.clean(doc['question_content'], strip=True)[:500]

            result = {
                'title': doc['question_title'],
                'type': 'question',
                'last_updated': datetime.fromtimestamp(doc['updated']),
                'is_solved': doc['question_is_solved'],
                'num_answers': doc['question_num_answers'],
                'num_votes': doc['question_num_votes'],
                'num_votes_past_week': doc['question_num_votes_past_week']}

        elif doc['model'] == 'forums_thread':
            summary = _build_es_excerpt(doc, first_only=True)
            result = {
                'title': doc['post_title'],
                'type': 'thread'}

        else:
            raise UnknownDocType('%s is an unknown doctype' % doc['model'])

        result['url'] = doc['url']
        if not is_json:
            result['object'] = doc
        result['search_summary'] = summary
        result['rank'] = rank
        result['score'] = doc.es_meta.score
        result['explanation'] = escape(format_explanation(doc.es_meta.explanation))
        result['id'] = doc['id']
        results.append(result)

    return results


@markup_json
@handle_es_errors(_es_down_template)
def simple_search(request):
    """Elasticsearch-specific simple search view.

    This view is for end user searching of the Knowledge Base and
    Support Forum. Filtering options are limited to:

    * product (`product=firefox`, for example, for only Firefox results)
    * document type (`w=2`, for example, for Support Forum questions only)

    """

    to_json = JSONRenderer().render
    template = 'search/results.html'

    # 1. Prep request.
    # Redirect to old Advanced Search URLs (?a={1,2}) to the new URL.
    if request.GET.get('a') in ['1', '2']:
        new_url = reverse('search.advanced') + '?' + request.GET.urlencode()
        return HttpResponseRedirect(new_url)

    # 2. Build form.
    search_form = SimpleSearchForm(request.GET, auto_id=False)

    # 3. Validate request.
    if not search_form.is_valid():
        if request.IS_JSON:
            return HttpResponse(
                json.dumps({'error': _('Invalid search data.')}),
                content_type=request.CONTENT_TYPE,
                status=400)

        t = 'search/form.html'
        return cache_control(
            render(request, t, {
                'advanced': False,
                'request': request,
                'search_form': search_form}),
            settings.SEARCH_CACHE_PERIOD)

    # 4. Generate search.
    cleaned = search_form.cleaned_data

    # On mobile, we default to just wiki results.
    if request.MOBILE and cleaned['w'] == constants.WHERE_BASIC:
        cleaned['w'] = constants.WHERE_WIKI

    language = locale_or_default(cleaned['language'] or request.LANGUAGE_CODE)
    lang_name = settings.LANGUAGES_DICT.get(language.lower()) or ''

    searcher = generate_simple_search(search_form, language, with_highlights=True)
    searcher = searcher[:settings.SEARCH_MAX_RESULTS]

    # 5. Generate output.
    pages = paginate(request, searcher, settings.SEARCH_RESULTS_PER_PAGE)

    if pages.paginator.count == 0:
        fallback_results = _fallback_results(language, cleaned['product'])
        results = []

    else:
        fallback_results = None
        results = build_results_list(pages, request.IS_JSON)

    product = Product.objects.filter(slug__in=cleaned['product'])
    if product:
        product_titles = [pgettext('DB: products.Product.title', p.title) for p in product]
    else:
        product_titles = [_('All Products')]

    # FIXME: This is probably bad l10n.
    product_titles = ', '.join(product_titles)

    data = {
        'num_results': pages.paginator.count,
        'results': results,
        'fallback_results': fallback_results,
        'product_titles': product_titles,
        'q': cleaned['q'],
        'w': cleaned['w'],
        'lang_name': lang_name,
        'products': Product.objects.filter(visible=True)}

    if request.IS_JSON:
        data['total'] = len(data['results'])
        data['products'] = [{'slug': p.slug, 'title': p.title}
                            for p in data['products']]

        if product:
            data['product'] = product[0].slug

        pages = Paginator(pages)
        data['pagination'] = dict(
            number=pages.pager.number,
            num_pages=pages.pager.paginator.num_pages,
            has_next=pages.pager.has_next(),
            has_previous=pages.pager.has_previous(),
            max=pages.max,
            span=pages.span,
            dotted_upper=pages.pager.dotted_upper,
            dotted_lower=pages.pager.dotted_lower,
            page_range=pages.pager.page_range,
            url=pages.pager.url,
        )
        if not results:
            data['message'] = _('No pages matched the search criteria')

        json_data = to_json(data)
        if request.JSON_CALLBACK:
            json_data = request.JSON_CALLBACK + '(' + json_data + ');'
        return HttpResponse(json_data, content_type=request.CONTENT_TYPE)

    data.update({
        'product': product,
        'pages': pages,
        'search_form': search_form,
        'advanced': False,
    })
    resp = cache_control(render(request, template, data), settings.SEARCH_CACHE_PERIOD)
    resp.set_cookie(settings.LAST_SEARCH_COOKIE, urlquote(cleaned['q']),
                    max_age=3600, secure=False, httponly=False)
    return resp


@markup_json
@handle_es_errors(_es_down_template)
def advanced_search(request):
    """Elasticsearch-specific Advanced search view"""

    to_json = JSONRenderer().render
    template = 'search/results.html'

    # 1. Prep request.
    r = request.GET.copy()
    # TODO: Figure out how to get rid of 'a' and do it.
    # It basically is used to switch between showing the form or results.
    a = request.GET.get('a', '2')
    # TODO: This is so the 'a=1' stays in the URL for pagination.
    r['a'] = 1

    language = locale_or_default(request.GET.get('language', request.LANGUAGE_CODE))
    r['language'] = language
    lang = language.lower()
    lang_name = settings.LANGUAGES_DICT.get(lang) or ''

    # 2. Build form.
    search_form = AdvancedSearchForm(r, auto_id=False)
    search_form.set_allowed_forums(request.user)

    # 3. Validate request.
    # Note: a == 2 means "show the form"--that's all we use it for now.
    if a == '2' or not search_form.is_valid():
        if request.IS_JSON:
            return HttpResponse(
                json.dumps({'error': _('Invalid search data.')}),
                content_type=request.CONTENT_TYPE,
                status=400)

        t = 'search/form.html'
        data = {'advanced': True,
                'request': request,
                'search_form': search_form}
        # get value for search input from last search term.
        last_search = request.COOKIES.get(settings.LAST_SEARCH_COOKIE)
        # If there is any cached input from last search, pass it to template
        if last_search and 'q' not in r:
            cached_field = urlquote(last_search)
            data.update({'cached_field': cached_field})

        return cache_control(
            render(request, t, data),
            settings.SEARCH_CACHE_PERIOD)

    # 4. Generate search.
    cleaned = search_form.cleaned_data

    # On mobile, we default to just wiki results.
    if request.MOBILE and cleaned['w'] == constants.WHERE_BASIC:
        cleaned['w'] = constants.WHERE_WIKI

    # We use a regular S here because we want to search across
    # multiple doctypes.
    searcher = (AnalyzerS().es(urls=settings.ES_URLS,
                               timeout=settings.ES_TIMEOUT,
                               use_ssl=settings.ES_USE_SSL,
                               http_auth=settings.ES_HTTP_AUTH,
                               connection_class=RequestsHttpConnection)
                           .indexes(es_utils.read_index('default')))

    doctypes = []
    final_filter = F()
    unix_now = int(time.time())
    interval_filters = (
        ('created', cleaned['created'], cleaned['created_date']),
        ('updated', cleaned['updated'], cleaned['updated_date'])
    )

    # Start - wiki search configuration

    if cleaned['w'] & constants.WHERE_WIKI:
        wiki_f = F(model='wiki_document')

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
        if not cleaned['include_archived']:
            wiki_f &= F(document_is_archived=False)

        # Apply sortby
        sortby = cleaned['sortby_documents']
        try:
            searcher = searcher.order_by(*constants.SORT_DOCUMENTS[sortby])
        except IndexError:
            # Skip index errors because they imply the user is sending us sortby values
            # that aren't valid.
            pass

        doctypes.append(DocumentMappingType.get_mapping_type_name())
        final_filter |= wiki_f

    # End - wiki search configuration

    # Start - support questions configuration

    if cleaned['w'] & constants.WHERE_SUPPORT:
        question_f = F(model='questions_question')

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

        # Note: num_voted (with a d) is a different field than num_votes
        # (with an s). The former is a dropdown and the latter is an
        # integer value.
        if cleaned['num_voted'] == constants.INTERVAL_BEFORE:
            question_f &= F(question_num_votes__lte=max(cleaned['num_votes'], 0))
        elif cleaned['num_voted'] == constants.INTERVAL_AFTER:
            question_f &= F(question_num_votes__gte=cleaned['num_votes'])

        # Apply sortby
        sortby = cleaned['sortby']
        try:
            searcher = searcher.order_by(*constants.SORT_QUESTIONS[sortby])
        except IndexError:
            # Skip index errors because they imply the user is sending us sortby values
            # that aren't valid.
            pass

        # Apply created and updated filters
        for filter_name, filter_option, filter_date in interval_filters:
            if filter_option == constants.INTERVAL_BEFORE:
                before = {filter_name + '__gte': 0,
                          filter_name + '__lte': max(filter_date, 0)}

                question_f &= F(**before)

            elif filter_option == constants.INTERVAL_AFTER:
                after = {filter_name + '__gte': min(filter_date, unix_now),
                         filter_name + '__lte': unix_now}

                question_f &= F(**after)

        doctypes.append(QuestionMappingType.get_mapping_type_name())
        final_filter |= question_f

    # End - support questions configuration

    # Start - discussion forum configuration

    if cleaned['w'] & constants.WHERE_DISCUSSION:
        discussion_f = F(model='forums_thread')

        if cleaned['author']:
            discussion_f &= F(post_author_ord=cleaned['author'])

        if cleaned['thread_type']:
            if constants.DISCUSSION_STICKY in cleaned['thread_type']:
                discussion_f &= F(post_is_sticky=1)

            if constants.DISCUSSION_LOCKED in cleaned['thread_type']:
                discussion_f &= F(post_is_locked=1)

        valid_forum_ids = [f.id for f in Forum.authorized_forums_for_user(request.user)]

        forum_ids = None
        if cleaned['forum']:
            forum_ids = [f for f in cleaned['forum'] if f in valid_forum_ids]

        # If we removed all the forums they wanted to look at or if
        # they didn't specify, then we filter on the list of all
        # forums they're authorized to look at.
        if not forum_ids:
            forum_ids = valid_forum_ids

        discussion_f &= F(post_forum_id__in=forum_ids)

        # Apply created and updated filters
        for filter_name, filter_option, filter_date in interval_filters:
            if filter_option == constants.INTERVAL_BEFORE:
                before = {filter_name + '__gte': 0,
                          filter_name + '__lte': max(filter_date, 0)}

                discussion_f &= F(**before)

            elif filter_option == constants.INTERVAL_AFTER:
                after = {filter_name + '__gte': min(filter_date, unix_now),
                         filter_name + '__lte': unix_now}

                discussion_f &= F(**after)

        doctypes.append(ThreadMappingType.get_mapping_type_name())
        final_filter |= discussion_f

    # End - discussion forum configuration

    # Done with all the filtery stuff--time  to generate results

    searcher = searcher.doctypes(*doctypes)
    searcher = searcher.filter(final_filter)

    if 'explain' in request.GET and request.GET['explain'] == '1':
        searcher = searcher.explain()

    cleaned_q = cleaned['q']

    # Set up the highlights. Show the entire field highlighted.
    searcher = searcher.highlight(
        'question_content',  # support forum
        'document_summary',  # kb
        'post_content',  # contributor forum
        pre_tags=['<b>'],
        post_tags=['</b>'],
        number_of_fragments=0)

    searcher = apply_boosts(searcher)

    # Build the query
    if cleaned_q:
        query_fields = chain(*[
            cls.get_query_fields() for cls in [
                DocumentMappingType,
                ThreadMappingType,
                QuestionMappingType
            ]
        ])
        query = {}
        # Create a simple_query_search query for every field we want to search.
        for field in query_fields:
            query['%s__sqs' % field] = cleaned_q

        # Transform the query to use locale aware analyzers.
        query = es_utils.es_query_with_analyzer(query, language)

        searcher = searcher.query(should=True, **query)

    searcher = searcher[:settings.SEARCH_MAX_RESULTS]

    # 5. Generate output
    pages = paginate(request, searcher, settings.SEARCH_RESULTS_PER_PAGE)

    if pages.paginator.count == 0:
        # If we know there aren't any results, show fallback_results.
        fallback_results = _fallback_results(language, cleaned['product'])
        results = []
    else:
        fallback_results = None
        results = build_results_list(pages, request.IS_JSON)

    items = [(k, v) for k in search_form.fields for
             v in r.getlist(k) if v and k != 'a']
    items.append(('a', '2'))

    product = Product.objects.filter(slug__in=cleaned['product'])
    if product:
        product_titles = [pgettext('DB: products.Product.title', p.title) for p in product]
    else:
        product_titles = [_('All Products')]

    # FIXME: This is probably bad l10n.
    product_titles = ', '.join(product_titles)

    data = {
        'num_results': pages.paginator.count,
        'results': results,
        'fallback_results': fallback_results,
        'product_titles': product_titles,
        'q': cleaned['q'],
        'w': cleaned['w'],
        'lang_name': lang_name,
        'advanced': True,
        'products': Product.objects.filter(visible=True)
    }

    if request.IS_JSON:
        data['total'] = len(data['results'])
        data['products'] = [{'slug': p.slug, 'title': p.title}
                            for p in data['products']]

        if product:
            data['product'] = product[0].slug

        pages = Paginator(pages)
        data['pagination'] = dict(
            number=pages.pager.number,
            num_pages=pages.pager.paginator.num_pages,
            has_next=pages.pager.has_next(),
            has_previous=pages.pager.has_previous(),
            max=pages.max,
            span=pages.span,
            dotted_upper=pages.pager.dotted_upper,
            dotted_lower=pages.pager.dotted_lower,
            page_range=pages.pager.page_range,
            url=pages.pager.url,
        )
        if not results:
            data['message'] = _('No pages matched the search criteria')
        json_data = to_json(data)
        if request.JSON_CALLBACK:
            json_data = request.JSON_CALLBACK + '(' + json_data + ');'
        return HttpResponse(json_data, content_type=request.CONTENT_TYPE)

    data.update({
        'product': product,
        'pages': pages,
        'search_form': search_form
    })
    resp = cache_control(render(request, template, data), settings.SEARCH_CACHE_PERIOD)
    resp.set_cookie(settings.LAST_SEARCH_COOKIE, urlquote(cleaned['q']),
                    max_age=3600, secure=False, httponly=False)
    return resp


@cache_page(60 * 15)  # 15 minutes.
def opensearch_suggestions(request):
    """A simple search view that returns OpenSearch suggestions."""
    content_type = 'application/x-suggestions+json'
    search_form = SimpleSearchForm(request.GET, auto_id=False)
    if not search_form.is_valid():
        return HttpResponseBadRequest(content_type=content_type)

    cleaned = search_form.cleaned_data
    language = locale_or_default(cleaned['language'] or request.LANGUAGE_CODE)
    searcher = generate_simple_search(search_form, language, with_highlights=False)
    searcher = searcher.values_dict('document_title', 'question_title', 'url')
    results = searcher[:10]

    def urlize(r):
        return u'%s://%s%s' % (
            'https' if request.is_secure() else 'http',
            request.get_host(),
            r['url'][0]
        )

    def titleize(r):
        # NB: Elasticsearch returns an array of strings as the value, so we mimic that and
        # then pull out the first (and only) string.
        return r.get('document_title', r.get('question_title', [_('No title')]))[0]

    try:
        data = [
            cleaned['q'],
            [titleize(r) for r in results],
            [],
            [urlize(r) for r in results]
        ]
    except ES_EXCEPTIONS:
        # If we have Elasticsearch problems, we just send back an empty set of results.
        data = []

    return HttpResponse(json.dumps(data), content_type=content_type)


@cache_page(60 * 60 * 168)  # 1 week.
def opensearch_plugin(request):
    """Render an OpenSearch Plugin."""
    host = u'%s://%s' % ('https' if request.is_secure() else 'http', request.get_host())

    # Use `render_to_response` here instead of `render` because `render`
    # includes the request in the context of the response. Requests
    # often include the session, which can include pickable things.
    # `render_to_respones` doesn't include the request in the context.
    return render_to_response(
        'search/plugin.html', {
            'host': host,
            'locale': request.LANGUAGE_CODE
        },
        content_type='application/opensearchdescription+xml'
    )


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
    bits = [m.strip() for m in chain(*result.es_meta.highlight.values())]

    if first_only and bits:
        excerpt = bits[0]
    else:
        excerpt = EXCERPT_JOINER.join(bits)

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
