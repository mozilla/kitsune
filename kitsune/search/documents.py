from django.utils import timezone
from django_elasticsearch_dsl import DocType, fields

from kitsune.questions.models import Question, Answer
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


class QuestionDocumentType(KitsuneDocTypeMixin, DocType):
    url = fields.KeywordField(attr='get_absolute_url')
    indexed_on = fields.DateField()
    created = fields.DateField()
    updated = fields.DateField()

    product = fields.KeywordField(attr='product.slug')
    topic = fields.KeywordField(attr='topic.slug')

    # Document specific fields (locale aware)
    question_title = fields.TextField(attr='title')
    question_content = fields.TextField(attr='content', store=True,
                                        term_vector='with_positions_offsets')
    question_answer_content = fields.TextField()
    question_num_answers = fields.IntegerField(attr='num_answers')
    question_is_solved = fields.BooleanField(attr='is_solved')
    question_is_locked = fields.BooleanField(attr='is_locked')
    question_is_archived = fields.BooleanField(attr='is_archived')
    question_has_answers = fields.BooleanField()
    question_has_helpful = fields.BooleanField()
    question_creator = fields.KeywordField(attr='creator.username')
    question_answer_creator = fields.KeywordField()
    question_num_votes = fields.IntegerField(attr='num_votes')
    question_num_votes_past_week = fields.IntegerField(attr='num_votes_past_week')
    question_tag = fields.KeywordField()
    question_locale = fields.KeywordField(attr='locale')

    # Custom configuration for kitsune to have separate analyzer for supported locales
    supported_locales = settings.SUMO_LANGUAGES

    class Meta:
        model = Question
        index = config.QUESTION_INDEX_NAME

    def prepare_indexed_on(self, instance):
        return timezone.now()

    def prepare_question_answer_content(self, instance):
        return [a['content'] for a in instance.answer_values]

    def prepare_question_has_answers(self, instance):
        return bool(instance.num_answers)

    def prepare_question_has_helpful(self, instance):
        if instance.answer_values:
            return instance.answer_values.filter(votes__helpful=True).exists()

        return False

    def prepare_question_answer_creator(self, instance):
        return [a['creator__username'] for a in instance.answer_values]

    def prepare_question_tag(self, instance):
        return [tag.name for tag in instance.my_tags]


class AnswerDocumentType(KitsuneDocTypeMixin, DocType):

    url = fields.KeywordField(attr='get_absolute_url')
    indexed_on = fields.DateField()
    created = fields.DateField()

    locale = fields.KeywordField(attr='question.locale')
    is_solution = fields.BooleanField()
    creator_id = fields.IntegerField(attr='creator.id')
    by_asker = fields.BooleanField()
    helpful_count = fields.IntegerField(attr='num_helpful_votes')
    unhelpful_count = fields.IntegerField(attr='num_unhelpful_votes')

    product = fields.KeywordField(attr='question.product.slug')
    topic = fields.KeywordField(attr='product.slug')

    # Custom configuration for kitsune to have separate analyzer for supported locales
    supported_locales = settings.SUMO_LANGUAGES
    locale_field = 'question__locale'

    def prepare_indexed_on(self, instance):
        return timezone.now()

    def prepare_is_solution(self, instance):
        return instance.id == instance.question.solution_id

    def prepare_by_asker(self, instance):
        return instance.creator_id == instance.question.creator_id

    class Meta:
        model = Answer
        index = 'sumo_answer'
