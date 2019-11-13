from django.utils import timezone

from elasticsearch_dsl import field, Document as DSLDocument

from kitsune.search import config
from kitsune.search.fields import WikiLocaleText
from kitsune.wiki.config import REDIRECT_HTML


class WikiDocument(DSLDocument):
    url = field.Keyword()
    indexed_on = field.Date()
    updated = field.Date()

    product = field.Keyword()
    topic = field.Keyword()

    # Document specific fields (locale aware)
    title = WikiLocaleText()
    keywords = WikiLocaleText()
    content = WikiLocaleText(store=True, term_vector='with_positions_offsets',)
    summary = WikiLocaleText(store=True, term_vector='with_positions_offsets')

    locale = field.Keyword()
    current_id = field.Integer()
    parent_id = field.Integer()
    category = field.Integer()
    slug = field.Keyword()
    is_archived = field.Boolean()
    recent_helpful_votes = field.Integer()
    document_display_order = field.Integer()

    class Index:
        name = config.WIKI_DOCUMENT_INDEX_NAME

    def prepare_url(self, instance):
        return instance.get_absolute_url()

    def prepare_indexed_on(self, instance):
        return timezone.now()

    def prepare_updated(self, instance):
        return getattr(instance.current_revision, 'created', None)

    def prepare_product(self, instance):
        return [t.slug for t in instance.get_products()]

    def prepare_topic(self, instance):
        return [t.slug for t in instance.get_topics()]

    def prepare_keywords(self, instance):
        return getattr(instance.current_revision, 'keywords', None)

    def prepare_content(self, instance):
        return instance.html

    def prepare_summary(self, instance):
        if instance.current_revision:
            return instance.summary
        return None

    def prepare_current_id(self, instance):
        if instance.current_revision:
            return instance.current_revision.id
        return None

    def prepare_parent_id(self, instance):
        if instance.parent:
            return instance.parent.id
        return None

    def prepare_recent_helpful_votes(self, instance):
        # Don't extract helpful votes if the document doesn't have a current
        # revision, or is a template, or is a redirect, or is in Navigation
        # category (50).
        if instance.current_revision and not (instance.is_template and
                                              instance.html.startswith(REDIRECT_HTML) and
                                              instance.category == 50):
            return instance.recent_helpful_votes
        return 0

    def prepare_display_order(self, instance):
        return instance.original.display_order

    def prepare(self, instance):
        """Prepare an ES WikiDocument object given a model instance"""
        kwargs = []
        fields = self.__dict__.keys()

        for f in fields:
            try:
                prepare_method = getattr(self, 'prepare_{}'.format(field))
                kwargs[field] = prepare_method(instance)
            except AttributeError:
                kwargs[field] = getattr(instance, field)
        return kwargs
