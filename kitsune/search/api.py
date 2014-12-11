import itertools

from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response

from kitsune.products.models import Product
from kitsune.questions.models import QuestionMappingType
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

    wiki_f = es_utils.F(
        model='wiki_document',
        document_category__in=settings.SEARCH_DEFAULT_CATEGORIES,
        document_locale=locale,
        document_is_archived=False)

    questions_f = es_utils.F(
        model='questions_question',
        question_is_archived=False,
        question_is_locked=False,
        question_has_helpful=True)

    if product is not None:
        wiki_f &= es_utils.F(product=product)
        questions_f &= es_utils.F(product=product)

    mapping_types = [QuestionMappingType, DocumentMappingType]
    query_fields = itertools.chain(*[cls.get_query_fields() for cls in mapping_types])
    query = {}
    for field in query_fields:
        for query_type in ['match', 'match_phrase']:
            key = '{0}__{1}'.format(field, query_type)
            query[key] = text

    # Transform query to be locale aware.
    query = es_utils.es_query_with_analyzer(query, locale)

    query = dict(('%s__match' % field, 'emails')
                 for field in QuestionMappingType.get_query_fields())

    searcher = (
        es_utils.AnalyzerS()
        .es(urls=settings.ES_URLS)
        .indexes(es_utils.read_index('default'))
        .doctypes(*[cls.get_mapping_type_name() for cls in mapping_types])
        .filter(wiki_f | questions_f)
        .query(should=True, **query))

    documents = []
    questions = []

    for result in searcher[:(max_documents + max_questions) * 2]:
        if result['model'] == 'wiki_document':
            documents.append({
                'title': result['document_title'],
                'slug': result['document_slug'],
                'summary': result['document_summary'],
            })
        elif result['model'] == 'questions_question':
            questions.append({
                'id': result['id'],
                'title': result['question_title'],
            })
        if len(documents) >= max_documents and len(questions) >= max_questions:
            break

    return Response({
        'questions': questions[:max_questions],
        'documents': documents[:max_documents],
    })
