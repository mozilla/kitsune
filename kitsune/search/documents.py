from django.conf import settings
from django.utils import timezone
from elasticsearch_dsl import field, Document as DSLDocument
from elasticsearch_dsl.query import Terms, Term, MultiMatch, Bool

from kitsune.search import config
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.wiki.models import Document
from .fields import WikiLocaleText


class WikiDocument(DSLDocument):
    url = field.Keyword()
    indexed_on = field.Date()
    updated = field.Date()

    product = field.Keyword()
    topic = field.Keyword()

    # Document specific fields (locale aware)
    document_title = WikiLocaleText()
    document_keywords = WikiLocaleText()
    document_content = WikiLocaleText(store=True, term_vector='with_positions_offsets',)
    document_summary = WikiLocaleText(store=True, term_vector='with_positions_offsets')

    document_locale = field.Keyword()
    document_current_id = field.Integer()
    document_parent_id = field.Integer()
    document_category = field.Integer()
    document_slug = field.Keyword()
    document_is_archived = field.Boolean()
    document_recent_helpful_votes = field.Integer()
    document_display_order = field.Integer()

    # Store the index name to the index until elastic/elasticsearch#23306 get fixed
    # https://github.com/elastic/elasticsearch/issues/23306
    index_name = field.Keyword()

    class Index:
        name = config.WIKI_DOCUMENT_INDEX_NAME

    def prepare_indexed_on(self, instance):
        return timezone.now()

    def prepare_updated(self, instance):
        return getattr(instance.current_revision, 'created', None)

    def prepare_topic(self, instance):
        return [t.slug for t in instance.get_topics()]

    def prepare_product(self, instance):
        return [t.slug for t in instance.get_products()]

    def prepare_document_keywords(self, instance):
        return getattr(instance.current_revision, 'keywords', None)

    def prepare_document_summary(self, instance):
        if instance.current_revision:
            return instance.summary

    def prepare_document_recent_helpful_votes(self, instance):
        if instance.current_revision and not (instance.is_template and
                                              instance.html.startswith(REDIRECT_HTML) and
                                              instance.category == 50):

            return instance.recent_helpful_votes
        else:
            return 0

    def prepare_index_name(self, instance):
        return config.WIKI_DOCUMENT_INDEX_NAME

    # methods for kitsune usages
    @classmethod
    def get_filters(cls, locale, products=None, categories=None, topics=None):
        categories = categories or settings.SEARCH_DEFAULT_CATEGORIES
        yield Terms(document_category=categories)
        yield Term(document_locale=locale)
        yield Term(document_is_archived=False)
        yield Term(index_name=config.WIKI_DOCUMENT_INDEX_NAME)

        if products:
            yield cls.get_product_filters(products=products)
        if topics:
            yield Terms(topic=topics)

    @classmethod
    def get_query(cls, query, locale, products=None, categories=None):
        common_fields = ['document_summary^2.0', 'document_keywords^8.0']
        match_fields = common_fields + ['document_title^6.0', 'document_content^1.0']
        match_phrase_fields = common_fields + ['document_title^10.0', 'document_content^8.0']

        match_query = MultiMatch(query=query, fields=match_fields)
        # Its also a multi match query, but its phrase type.
        # Which actually run phrase query among the fields.
        # https://bit.ly/2DB1qgH
        match_phrase_query = MultiMatch(query=query,
                                        fields=match_phrase_fields,
                                        type="phrase")

        filters = list(cls.get_filters(locale=locale, products=products, categories=categories))
        bool_query = Bool(should=[match_query, match_phrase_query], filter=filters,
                          minimum_should_match=1)

        return bool_query
