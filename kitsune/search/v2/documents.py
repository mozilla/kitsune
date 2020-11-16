from django.db.models import Count, Prefetch, Q
from elasticsearch_dsl import InnerDoc, connections, field

from kitsune.forums.models import Post
from kitsune.questions.models import Answer, Question
from kitsune.search import config
from kitsune.search.v2.base import SumoDocument
from kitsune.search.v2.es7_utils import es7_client
from kitsune.search.v2.fields import (
    SumoLocaleAwareBooleanField,
    SumoLocaleAwareKeywordField,
    SumoLocaleAwareTextField,
)
from kitsune.users.models import Profile
from kitsune.wiki import models as wiki_models

connections.add_connection(config.DEFAULT_ES7_CONNECTION, es7_client())


class WikiDocument(SumoDocument):
    updated = field.Date()

    product_ids = field.Keyword(multi=True)
    topic_ids = field.Keyword(multi=True)
    locale = field.Keyword()
    category = field.Keyword()

    # Document specific fields (locale aware)
    title = SumoLocaleAwareTextField()
    content = SumoLocaleAwareTextField(store=True, term_vector="with_positions_offsets")
    summary = SumoLocaleAwareTextField(store=True, term_vector="with_positions_offsets")
    keywords = SumoLocaleAwareKeywordField(multi=True)
    slug = SumoLocaleAwareKeywordField(store=True)
    doc_id = SumoLocaleAwareKeywordField(store=True)
    is_archived = SumoLocaleAwareBooleanField()

    class Index:
        name = config.WIKI_DOCUMENT_INDEX_NAME
        using = config.DEFAULT_ES7_CONNECTION

    @classmethod
    def prepare(cls, instance):
        """Override super method to merge docs for KB."""
        return super(WikiDocument, cls).prepare(instance, merge_docs=True)

    def prepare_updated(self, instance):
        return getattr(instance.current_revision, "created", None)

    def prepare_keywords(self, instance):
        """Return a list of keywords, splitted by space or None"""
        return getattr(instance.current_revision, "keywords", "").split() or None

    def prepare_content(self, instance):
        return instance.html

    def prepare_summary(self, instance):
        if instance.current_revision:
            return instance.summary
        return None

    def prepare_doc_id(self, instance):
        return instance.pk

    def prepare_topic_ids(self, instance):
        return [topic.id for topic in instance.topics.all()]

    def prepare_product_ids(self, instance):
        return [product.id for product in instance.products.all()]

    def prepare_parent_id(self, instance):
        if instance.parent:
            return instance.parent.id
        return None

    def prepare_display_order(self, instance):
        return instance.original.display_order

    @classmethod
    def get_model(cls):
        return wiki_models.Document


class QuestionDocument(SumoDocument):
    """
    ES document for Questions. Every Question in DB gets a QuestionDocument in ES.

    Parent class to AnswerDocument, with most fields here prefixed with "question_".

    This document defines the question-specific fields (most of) which are de-normalized
    in the AnswerDocument. Since QuestionDocument and AnswerDocument are stored in the
    same index, ES sees QuestionDocuments and AnswerDocuments the same, just with some
    documents missing certain fields.

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

    Child class to QuestionDocument, with fields here un-prefixed.

    This document defines the answer-specific fields which are included in an AnswerDocument
    in addition to the de-normalized fields of an Answer's Question which are defined in
    QuestionDocument. Since QuestionDocument and AnswerDocument are stored in the same index,
    ES sees QuestionDocuments and AnswerDocuments the same, just with some documents missing
    certain fields.

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
    def prepare(cls, instance, **kwargs):
        obj = super().prepare(instance, **kwargs)
        # add a prefix to the id so we don't clash with QuestionDocuments
        obj.meta.id = "a_{}".format(obj.meta.id)
        return obj

    @classmethod
    def get(cls, id, **kwargs):
        # if the id is un-prefixed, add it
        if not str(id).startswith("a_"):
            id = "a_{}".format(id)
        return super().get(id, **kwargs)

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
