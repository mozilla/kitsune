from django.db.models import Count, Prefetch, Q
from elasticsearch_dsl import InnerDoc, connections, field

from kitsune.forums.models import Post
from kitsune.questions.models import Answer, Question
from kitsune.search import config
from kitsune.search.v2.base import SumoDocument
from kitsune.search.v2.es7_utils import es7_client
from kitsune.search.v2.fields import SumoLocaleAwareTextField
from kitsune.users.models import Profile
from kitsune.wiki import models as wiki_models
from kitsune.wiki.config import REDIRECT_HTML

connections.add_connection(config.DEFAULT_ES7_CONNECTION, es7_client())


class WikiDocument(SumoDocument):
    url = field.Keyword()
    updated = field.Date()

    product_ids = field.Keyword(multi=True)
    topic_ids = field.Keyword(multi=True)

    # Document specific fields (locale aware)
    title = SumoLocaleAwareTextField()
    content = SumoLocaleAwareTextField(store=True, term_vector="with_positions_offsets")
    summary = SumoLocaleAwareTextField(store=True, term_vector="with_positions_offsets")
    keywords = SumoLocaleAwareTextField(multi=True)

    locale = field.Keyword()
    current_id = field.Integer()
    parent_id = field.Integer()
    category = field.Keyword()
    slug = field.Keyword()
    is_archived = field.Boolean()
    recent_helpful_votes = field.Integer()

    class Index:
        name = config.WIKI_DOCUMENT_INDEX_NAME
        using = config.DEFAULT_ES7_CONNECTION

    def prepare_url(self, instance):
        return instance.get_absolute_url()

    def prepare_updated(self, instance):
        return getattr(instance.current_revision, "created", None)

    def prepare_keywords(self, instance):
        return getattr(instance.current_revision, "keywords", None)

    def prepare_content(self, instance):
        return instance.html

    def prepare_summary(self, instance):
        if instance.current_revision:
            return instance.summary
        return None

    def prepare_product_ids(self, instance):
        return [product.id for product in instance.products.all()]

    def prepare_topic_ids(self, instance):
        return [topic.id for topic in instance.topics.all()]

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
        if instance.current_revision and not (
            instance.is_template
            and instance.html.startswith(REDIRECT_HTML)
            and instance.category == 50
        ):
            return instance.recent_helpful_votes
        return 0

    def prepare_display_order(self, instance):
        return instance.original.display_order

    @classmethod
    def get_model(cls):
        return wiki_models.Document


class QuestionDocument(SumoDocument):
    """
    ES document for Questions. Every Question in DB gets a QuestionDocument in ES.

    Parent class to AnswerDocument, so most fields are prefixed with "question_".
    QuestionDocument and AnswerDocument are stored in the same index, so QuestionDocument
    cannot define a field with the same name as AnswerDocument.
    Distinguish QuestionDocuments from AnswerDocuments by filtering on whether the
    document has a null "created" field.

    Enables searching for AAQ threads as a unit.
    """

    question_id = field.Keyword()

    question_title = SumoLocaleAwareTextField()
    question_creator_id = field.Keyword()
    question_content = SumoLocaleAwareTextField(term_vector="with_positions_offsets")

    question_created = field.Date()
    question_updated = field.Date()
    question_updated_by_id = field.Keyword()
    question_has_solution = field.Boolean()
    question_is_locked = field.Boolean()
    question_is_archived = field.Boolean()

    question_is_spam = field.Boolean()
    question_marked_as_spam = field.Date()
    question_marked_as_spam_by_id = field.Keyword()

    question_product_id = field.Keyword()
    question_topic_id = field.Keyword()

    question_taken_by_id = field.Keyword()
    question_taken_until = field.Date()

    question_tag_ids = field.Keyword(multi=True)
    question_num_votes = field.Integer()

    # store answer content to optimise searching for AAQ threads as a unit
    answer_content = SumoLocaleAwareTextField(multi=True, term_vector="with_positions_offsets")

    locale = field.Keyword()

    class Index:
        name = config.QUESTION_INDEX_NAME
        using = config.DEFAULT_ES7_CONNECTION

    def prepare_question_tag_ids(self, instance):
        return [tag.id for tag in instance.tags.all()]

    def prepare_question_has_solution(self, instance):
        return instance.solution_id is not None

    def prepare_question_num_votes(self, instance):
        if hasattr(instance, "es_question_num_votes"):
            return instance.es_question_num_votes
        return instance.num_votes

    def prepare_answer_content(self, instance):
        return [answer.content for answer in instance.answers.all()]

    def get_field_value(self, field, *args):
        if field.startswith("question_"):
            field = field[len("question_") :]
        return super().get_field_value(field, *args)

    @classmethod
    def get_model(cls):
        return Question

    @classmethod
    def get_queryset(cls):
        return (
            Question.objects.prefetch_related("answers")
            # prefetch tags to avoid extra queries when iterating over them
            .prefetch_related("tags")
            # count votes in db to improve performance
            .annotate(es_question_num_votes=Count("votes"))
        )


class AnswerDocument(QuestionDocument):
    """
    ES document for Answers. Every Answer in DB gets an AnswerDocument in ES.

    Child class to QuestionDocument and stored in the same index, so AnswerDocument
    cannot define a field with the same name as one in QuestionDocument.
    Most QuestionDocument fields are prefixed by "question_".
    Distingish AnswerDocuments from QuestionDocuments by filtering on whether the document
    has a non-null "created" field.

    Enables aggregations on answers, such as when creating contribution metrics, and enables
    searching within an AAQ thread, or on Answer-specific properties like being a solution.
    """

    creator_id = field.Keyword()
    created = field.Date()
    content = SumoLocaleAwareTextField(term_vector="with_positions_offsets")
    updated = field.Date()
    updated_by_id = field.Keyword()

    is_spam = field.Boolean()
    marked_as_spam = field.Date()
    marked_as_spam_by_id = field.Keyword()

    num_helpful_votes = field.Integer()
    num_unhelpful_votes = field.Integer()

    is_solution = field.Boolean()

    def prepare_is_solution(self, instance):
        solution_id = instance.question.solution_id
        return solution_id is not None and solution_id == instance.id

    def prepare_locale(self, instance):
        return instance.question.locale

    def prepare_num_helpful_votes(self, instance):
        if hasattr(instance, "es_num_helpful_votes"):
            return instance.es_num_helpful_votes
        return instance.num_helpful_votes

    def prepare_num_unhelpful_votes(self, instance):
        if hasattr(instance, "es_num_unhelpful_votes"):
            return instance.es_num_unhelpful_votes
        return instance.num_unhelpful_votes

    def prepare_answer_content(self, instance):
        # clear answer_content field from QuestionDocument,
        # as we don't need the content of sibling answers in an AnswerDocument
        return None

    def get_field_value(self, field, instance, *args):
        if field.startswith("question_"):
            instance = instance.question
        return super().get_field_value(field, instance, *args)

    @classmethod
    def get_model(cls):
        return Answer

    @classmethod
    def get_queryset(cls):
        return (
            Answer.objects
            # prefetch each answer's question,
            # applying the same optimizations as in the QuestionDocument
            .prefetch_related(Prefetch("question", queryset=QuestionDocument.get_queryset()))
            # count votes in db to improve performance
            .annotate(
                es_num_helpful_votes=Count("votes", filter=Q(votes__helpful=True)),
                es_num_unhelpful_votes=Count("votes", filter=Q(votes__helpful=False)),
            )
        )


class ProfileDocument(SumoDocument):
    username = field.Keyword(normalizer="lowercase")
    name = field.Text(fields={"keyword": field.Keyword()})
    email = field.Keyword()
    # store avatar url so we don't need to hit the db when searching users
    # but set enabled=False to ensure ES does no parsing of it
    avatar = field.Object(enabled=False)

    timezone = field.Keyword()
    country = field.Keyword()
    locale = field.Keyword()

    involved_from = field.Date()

    product_ids = field.Keyword(multi=True)
    group_ids = field.Keyword(multi=True)

    class Index:
        name = config.USER_INDEX_NAME
        using = config.DEFAULT_ES7_CONNECTION

    def prepare_username(self, instance):
        return instance.user.username

    def prepare_email(self, instance):
        if instance.public_email:
            return instance.user.email

    def prepare_avatar(self, instance):
        if avatar := instance.fxa_avatar:
            return InnerDoc(url=avatar)

    def prepare_timezone(self, instance):
        return instance.timezone.zone if instance.timezone else None

    def prepare_product_ids(self, instance):
        return [product.id for product in instance.products.all()]

    def prepare_group_ids(self, instance):
        return [group.id for group in instance.user.groups.all()]

    @classmethod
    def get_model(cls):
        return Profile

    @classmethod
    def get_queryset(cls):
        return Profile.objects.select_related("user").prefetch_related("products", "user__groups")


class ForumDocument(SumoDocument):
    """
    ES document for forum posts. Thread information is duplicated across all posts in that thread.
    """

    thread_title = field.Text()
    thread_forum_id = field.Keyword()
    thread_created = field.Date()
    thread_creator_id = field.Keyword()
    thread_is_locked = field.Boolean()
    thread_is_sticky = field.Boolean()

    content = field.Text()
    author_id = field.Keyword()
    created = field.Date()
    updated = field.Date()
    updated_by_id = field.Keyword()

    class Index:
        name = config.FORUM_INDEX_NAME
        using = config.DEFAULT_ES7_CONNECTION

    def get_field_value(self, field, instance, *args):
        if field.startswith("thread_"):
            instance = instance.thread
            field = field[len("thread_") :]
        return super().get_field_value(field, instance, *args)

    @classmethod
    def get_model(cls):
        return Post

    @classmethod
    def get_queryset(cls):
        return Post.objects.select_related("thread")
