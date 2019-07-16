from itertools import chain

from django.conf import settings

from elasticsearch import RequestsHttpConnection

from kitsune import search as constants
from kitsune.questions.models import QuestionMappingType
from kitsune.search import es_utils
from kitsune.wiki.models import DocumentMappingType


def apply_boosts(searcher):
    """Returns searcher with boosts applied"""
    return searcher.boost(
        question_title=4.0,
        question_content=3.0,
        question_answer_content=3.0,
        post_title=2.0,
        post_content=1.0,
        document_title=6.0,
        document_content=1.0,
        document_keywords=8.0,
        document_summary=2.0,

        # Text phrases in document titles and content get an extra boost.
        document_title__match_phrase=10.0,
        document_content__match_phrase=8.0)


def generate_simple_search(search_form, language, with_highlights=False):
    """Generates an S given a form

    :arg search_form: a validated SimpleSearch form
    :arg language: the language code
    :arg with_highlights: whether or not to ask for highlights

    :returns: a fully formed S

    """
    # We use a regular S here because we want to search across
    # multiple doctypes.
    searcher = (
        es_utils.AnalyzerS().es(
            urls=settings.ES_URLS,
            timeout=settings.ES_TIMEOUT,
            use_ssl=settings.ES_USE_SSL,
            http_auth=settings.ES_HTTP_AUTH,
            connection_class=RequestsHttpConnection
        )
        .indexes(es_utils.read_index('default'))
    )

    cleaned = search_form.cleaned_data

    doctypes = []
    final_filter = es_utils.F()
    cleaned_q = cleaned['q']
    products = cleaned['product']

    # Handle wiki filters
    if cleaned['w'] & constants.WHERE_WIKI:
        wiki_f = es_utils.F(model='wiki_document',
                            document_category__in=settings.SEARCH_DEFAULT_CATEGORIES,
                            document_locale=language,
                            document_is_archived=False)

        for p in products:
            wiki_f &= es_utils.F(product=p)

        doctypes.append(DocumentMappingType.get_mapping_type_name())
        final_filter |= wiki_f

    # Handle question filters
    if cleaned['w'] & constants.WHERE_SUPPORT:
        question_f = es_utils.F(model='questions_question',
                                question_is_archived=False,
                                question_has_helpful=True)

        for p in products:
            question_f &= es_utils.F(product=p)

        doctypes.append(QuestionMappingType.get_mapping_type_name())
        final_filter |= question_f

    # Build a filter for those filters and add the other bits to
    # finish the search
    searcher = searcher.doctypes(*doctypes)
    searcher = searcher.filter(final_filter)

    if cleaned['explain']:
        searcher = searcher.explain()

    if with_highlights:
        # Set up the highlights. Show the entire field highlighted.
        searcher = searcher.highlight(
            'question_content',  # support forum
            'document_summary',  # kb
            pre_tags=['<b>'],
            post_tags=['</b>'],
            number_of_fragments=0
        )

    searcher = apply_boosts(searcher)

    # Build the query
    query_fields = chain(*[
        cls.get_query_fields() for cls in [
            DocumentMappingType,
            QuestionMappingType
        ]
    ])
    query = {}
    # Create match and match_phrase queries for every field
    # we want to search.
    for field in query_fields:
        for query_type in ['match', 'match_phrase']:
            query['%s__%s' % (field, query_type)] = cleaned_q

    # Transform the query to use locale aware analyzers.
    query = es_utils.es_query_with_analyzer(query, language)

    searcher = searcher.query(should=True, **query)
    return searcher
