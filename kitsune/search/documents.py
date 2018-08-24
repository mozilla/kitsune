from django.utils import timezone
from django_elasticsearch_dsl import DocType, Index, fields

from kitsune.search import config
from django.conf import settings

from kitsune.search.mixins import KitsuneDocTypeMixin
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.wiki.models import Document


class WikiDocumentType(KitsuneDocTypeMixin, DocType):
    url = fields.KeywordField(attr='get_absolute_url')
    indexed_on = fields.DateField()
    updated = fields.DateField()

    product = fields.KeywordField()
    topic = fields.KeywordField()

    # Document specific fields (locale aware)
    document_title = fields.TextField(attr='title')
    document_keywords = fields.TextField()
    document_content = fields.TextField(store=True, term_vector='with_positions_offsets',
                                        attr='html')
    document_summary = fields.TextField(store=True, term_vector='with_positions_offsets')

    document_locale = fields.KeywordField(attr='locale')
    document_current_id = fields.IntegerField(attr='current_revision_id')
    document_parent_id = fields.IntegerField(attr='parent_id')
    document_category = fields.IntegerField(attr='category')
    document_slug = fields.KeywordField(attr='slug')
    document_is_archived = fields.BooleanField(attr='is_archived')
    document_recent_helpful_votes = fields.IntegerField()
    document_display_order = fields.IntegerField(attr='original.display_order')

    # Custom configuration for kitsune to have separate analyzer for supported locales
    supported_locales = settings.SUMO_LANGUAGES

    class Meta:
        model = Document
        index = config.WIKI_DOCUMENT_INDEX_NAME

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
