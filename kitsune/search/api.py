from django.conf import settings

from elasticsearch import RequestsHttpConnection
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from kitsune.products.models import Product
from kitsune.questions.models import Question, QuestionMappingType
from kitsune.questions.api import QuestionSerializer
from kitsune.search import es_utils
from kitsune.sumo.api_utils import GenericAPIException
from kitsune.wiki.api import DocumentDetailSerializer
from kitsune.wiki.models import Document, DocumentMappingType


def positive_integer(value):
    if value < 0:
        raise serializers.ValidationError('This field must be positive.')


def valid_product(value):
    if not value:
        return

    if not Product.objects.filter(slug=value).exists():
        raise serializers.ValidationError(
            'Could not find product with slug "{0}".'.format(value)
        )


def valid_locale(value):
    if not value:
        return

    if value not in settings.SUMO_LANGUAGES:
        if value in settings.NON_SUPPORTED_LOCALES:
            fallback = settings.NON_SUPPORTED_LOCALES[value] or settings.WIKI_DEFAULT_LANGUAGE
            raise serializers.ValidationError(
                '"{0}" is not supported, but has fallback locale "{1}".'.format(
                    value, fallback))
        else:
            raise serializers.ValidationError(
                'Could not find locale "{0}".'.format(value)
            )


class SuggestSerializer(serializers.Serializer):
    q = serializers.CharField(required=True)
    locale = serializers.CharField(
        required=False, default=settings.WIKI_DEFAULT_LANGUAGE,
        validators=[valid_locale])
    product = serializers.CharField(
        required=False, default='',
        validators=[valid_product])
    max_questions = serializers.IntegerField(
        required=False, default=10,
        validators=[positive_integer])
    max_documents = serializers.IntegerField(
        required=False, default=10,
        validators=[positive_integer])


@api_view(['GET', 'POST'])
def suggest(request):
    if request.data and request.GET:
        raise GenericAPIException(
            400, 'Put all parameters either in the querystring or the HTTP request body.')

    serializer = SuggestSerializer(data=(request.data or request.GET))
    if not serializer.is_valid():
        raise GenericAPIException(400, serializer.errors)

    searcher = (
        es_utils.AnalyzerS()
        .es(urls=settings.ES_URLS,
            timeout=settings.ES_TIMEOUT,
            use_ssl=settings.ES_USE_SSL,
            http_auth=settings.ES_HTTP_AUTH,
            connection_class=RequestsHttpConnection)
        .indexes(es_utils.read_index('default')))

    data = serializer.validated_data

    return Response({
        'questions': _question_suggestions(
            searcher, data['q'], data['locale'], data['product'], data['max_questions']),
        'documents': _document_suggestions(
            searcher, data['q'], data['locale'], data['product'], data['max_documents']),
    })


def _question_suggestions(searcher, text, locale, product, max_results):
    if max_results <= 0:
        return []

    search_filter = es_utils.F(
        model='questions_question',
        question_is_archived=False,
        question_is_locked=False,
        question_is_solved=True)
    if product:
        search_filter &= es_utils.F(product=product)
    if locale:
        search_filter &= es_utils.F(question_locale=locale)

    questions = []
    searcher = _query(searcher, QuestionMappingType, search_filter, text, locale)

    question_ids = [result['id'] for result in searcher[:max_results]]
    questions = [
        QuestionSerializer(instance=q).data
        for q in Question.objects.filter(id__in=question_ids)
    ]

    return questions


def _document_suggestions(searcher, text, locale, product, max_results):
    if max_results <= 0:
        return []

    search_filter = es_utils.F(
        model='wiki_document',
        document_category__in=settings.SEARCH_DEFAULT_CATEGORIES,
        document_locale=locale,
        document_is_archived=False)

    if product:
        search_filter &= es_utils.F(product=product)

    documents = []
    searcher = _query(searcher, DocumentMappingType, search_filter, text, locale)

    doc_ids = [result['id'] for result in searcher[:max_results]]

    documents = [
        DocumentDetailSerializer(instance=doc).data
        for doc in Document.objects.filter(id__in=doc_ids)
    ]

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
