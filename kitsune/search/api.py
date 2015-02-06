from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response

from kitsune.products.models import Product
from kitsune.questions.models import Question, QuestionMappingType
from kitsune.questions.api import QuestionSerializer
from kitsune.search import es_utils
from kitsune.sumo.api import GenericAPIException
from kitsune.wiki.models import DocumentMappingType


@api_view(['GET', 'POST'])
def suggest(request):
    text = request.body or request.GET.get('q')
    locale = request.GET.get('locale', settings.WIKI_DEFAULT_LANGUAGE)
    product = request.GET.get('product')
    max_questions = request.GET.get('max_questions', 10)
    max_documents = request.GET.get('max_documents', 10)

    errors = {}
    try:
        max_questions = int(max_questions)
    except ValueError:
        errors['max_questions'] = 'This field must be an integer.'
    try:
        max_documents = int(max_documents)
    except ValueError:
        errors['max_documents'] = 'This field must be an integer.'
    if text is None:
        errors['q'] = 'This field is required.'
    if product is not None and not Product.objects.filter(slug=product).exists():
        errors['product'] = 'Could not find product with slug "{0}".'.format(product)
    if errors:
        raise GenericAPIException(400, errors)

    searcher = (
        es_utils.AnalyzerS()
        .es(urls=settings.ES_URLS)
        .indexes(es_utils.read_index('default')))

    return Response({
        'questions': _question_suggestions(searcher, text, locale, product, max_questions),
        'documents': _document_suggestions(searcher, text, locale, product, max_documents),
    })


def _question_suggestions(searcher, text, locale, product, max_results):
    search_filter = es_utils.F(
        model='questions_question',
        question_is_archived=False,
        question_is_locked=False,
        question_has_helpful=True)

    if product is not None:
        search_filter &= es_utils.F(product=product)

    questions = []
    searcher = _query(searcher, QuestionMappingType, search_filter, text, locale)

    for result in searcher[:max_results]:
        q = Question.objects.get(id=result['id'])
        questions.append(QuestionSerializer(instance=q).data)

    return questions


def _document_suggestions(searcher, text, locale, product, max_results):
    search_filter = es_utils.F(
        model='wiki_document',
        document_category__in=settings.SEARCH_DEFAULT_CATEGORIES,
        document_locale=locale,
        document_is_archived=False)

    if product is not None:
        search_filter &= es_utils.F(product=product)

    documents = []
    searcher = _query(searcher, DocumentMappingType, search_filter, text, locale)

    for result in searcher[:max_results]:
        documents.append({
            'title': result['document_title'],
            'slug': result['document_slug'],
            'summary': result['document_summary'],
        })

    return documents


def _query(searcher, mapping_type, search_filter, query_text, locale):
    query_fields = mapping_type.get_query_fields()
    query = {}
    for field in query_fields:
        for query_type in ['match', 'match_phrase']:
            key = '{0}__{1}'.format(field, query_type)
            query[key] = query_text

    # Transform query to be locale aware.
    query = es_utils.es_query_with_analyzer(query, locale)

    return (searcher
            .doctypes(mapping_type.get_mapping_type_name())
            .filter(search_filter)
            .query(should=True, **query))
