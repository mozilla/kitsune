from itertools import chain

from django.conf import settings
from django.utils.html import escape

from rest_framework import views
from rest_framework.response import Response

import bleach
import jinja2
from elasticutils.utils import format_explanation
from tower import ugettext as _, ugettext_lazy as _lazy

from kitsune.coolsearch.forms import SearchForm
from kitsune.forums.models import ThreadMappingType
from kitsune.questions.models import QuestionMappingType
from kitsune.search import es_utils
from kitsune.search.utils import locale_or_default, clean_excerpt, ComposedList
from kitsune.sumo.utils import smart_int
from kitsune.wiki.models import DocumentMappingType


EXCERPT_JOINER = _lazy(u'...', 'between search excerpts')


class SearchView(views.APIView):
    content_type = 'application/json'

    def get(self, request):
        data = self.get_data(request)
        status = None

        if isinstance(data, tuple):
            data = data[0]
            status = data[1]

        return Response(
            data,
            status=status,
            content_type=self.content_type,
        )

    def get_data(self, request):
        search_form = self.form_class(request.GET)
        if not search_form.is_valid():
            return (
                {'error': _('Invalid search data.')},
                400,
            )

        language = locale_or_default(
            request.GET.get('language', request.LANGUAGE_CODE)
        )
        lang = language.lower()
        if settings.LANGUAGES_DICT.get(lang):
            lang_name = settings.LANGUAGES_DICT[lang]
        else:
            lang_name = ''

        page = max(smart_int(request.GET.get('page')), 1)
        offset = (page - 1) * settings.SEARCH_RESULTS_PER_PAGE

        searcher = (
            es_utils.AnalyzerS()
            .es(urls=settings.ES_URLS)
            .indexes(es_utils.read_index('default'))
        )

        doctypes = self.get_doctypes()
        searcher = searcher.doctypes(*doctypes)

        filters = self.get_filters()
        searcher = searcher.filter(filters)

        # Add the simple string query.
        cleaned_q = search_form.cleaned_data.get('query')

        if cleaned_q:
            query_fields = self.get_query_fields()
            query = {}
            # Create a simple_query_search query for every field
            # we want to search.
            for field in query_fields:
                query['%s__sqs' % field] = cleaned_q

            # Transform the query to use locale aware analyzers.
            query = es_utils.es_query_with_analyzer(query, language)

            searcher = searcher.query(should=True, **query)

        try:
            num_results = min(searcher.count(), settings.SEARCH_MAX_RESULTS)

            results_per_page = settings.SEARCH_RESULTS_PER_PAGE

            # If we know there aren't any results, let's cheat and in
            # doing that, not hit ES again.
            if num_results == 0:
                searcher = []
            else:
                # TODO - Can ditch the ComposedList here, but we need
                # something that paginate can use to figure out the paging.
                documents = ComposedList()
                documents.set_count(('results', searcher), num_results)

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
                    searcher = searcher[bounds[0]:bounds[1]]

            results = []
            for i, doc in enumerate(searcher):
                rank = i + offset

                result = self.format_result(doc)

                result['url'] = doc['url']
                result['rank'] = rank
                result['score'] = doc.es_meta.score
                result['explanation'] = escape(
                    format_explanation(doc.es_meta.explanation)
                )
                result['id'] = doc['id']
                results.append(result)

        except es_utils.ES_EXCEPTIONS:
            return (
                {'error': _('Search Unavailable')},
                503,
            )

        data = {
            'num_results': num_results,
            'results': results,
            'lang_name': lang_name,
        }

        if not results:
            data['message'] = _('No pages matched the search criteria')

        return data

    def get_doctypes(self):
        raise NotImplementedError()

    def get_query_fields(self):
        raise NotImplementedError()

    def get_filters(self):
        raise NotImplementedError()

    def format_result(self, doc):
        raise NotImplementedError()


class SearchWikiView(SearchView):
    form_class = SearchForm

    def get_doctypes(self):
        return [DocumentMappingType.get_mapping_type_name()]

    def get_query_fields(self):
        return DocumentMappingType.get_query_fields()

    def get_filters(self):
        return es_utils.F()

    def format_result(self, doc):
        summary = _build_es_excerpt(doc)
        if not summary:
            summary = doc['document_summary']

        return {
            'title': doc['document_title'],
            'type': 'document',
            'search_summary': summary,
        }


class SearchQuestionView(SearchView):
    form_class = SearchForm

    def get_doctypes(self):
        return [QuestionMappingType.get_mapping_type_name()]

    def get_query_fields(self):
        return QuestionMappingType.get_query_fields()

    def get_filters(self):
        return es_utils.F()

    def format_result(self, doc):
        summary = _build_es_excerpt(doc)
        if not summary:
            # We're excerpting only question_content, so if
            # the query matched question_title or
            # question_answer_content, then there won't be any
            # question_content excerpts. In that case, just
            # show the question -- but only the first 500
            # characters.
            summary = bleach.clean(
                doc['question_content'], strip=True
            )[:500]

        return {
            'title': doc['question_title'],
            'type': 'question',
            'search_summary': summary,
            'is_solved': doc['question_is_solved'],
            'num_answers': doc['question_num_answers'],
            'num_votes': doc['question_num_votes'],
            'num_votes_past_week': doc['question_num_votes_past_week'],
        }


class SearchForumView(SearchView):
    form_class = SearchForm

    def get_doctypes(self):
        return [ThreadMappingType.get_mapping_type_name()]

    def get_query_fields(self):
        return ThreadMappingType.get_query_fields()

    def get_filters(self):
        return es_utils.F()

    def format_result(self, doc):
        summary = _build_es_excerpt(doc, first_only=True)
        return {
            'title': doc['post_title'],
            'type': 'thread',
            'search_summary': summary,
        }


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
