from django.db.models import Count, Prefetch, Q
from elasticsearch_dsl import InnerDoc, connections, field

from kitsune.forums.models import Post
from kitsune.questions.models import Answer, Question
from kitsune.search import config
from kitsune.search.v2.base import SumoDocument
from kitsune.search.v2.es7_utils import es7_client
from kitsune.search.v2.fields import SumoLocaleAwareKeywordField, SumoLocaleAwareTextField
from kitsune.users.models import Profile
from kitsune.wiki import models as wiki_models
from kitsune.wiki.config import CANNED_RESPONSES_CATEGORY, REDIRECT_HTML, TEMPLATES_CATEGORY

connections.add_connection(config.DEFAULT_ES7_CONNECTION, es7_client())


class WikiDocument(SumoDocument):
    updated = field.Date()

    product_ids = field.Keyword(multi=True)
    topic_ids = field.Keyword(multi=True)
    category = field.Keyword()

    # Document specific fields (locale aware)
    title = SumoLocaleAwareTextField()
    content = SumoLocaleAwareTextField(store=True, term_vector="with_positions_offsets")
    summary = SumoLocaleAwareTextField(store=True, term_vector="with_positions_offsets")
    # store keywords in a text field so they're stemmed:
    keywords = SumoLocaleAwareTextField()
    slug = SumoLocaleAwareKeywordField(store=True)
    doc_id = SumoLocaleAwareKeywordField(store=True)

    class Index:
        pass

    @classmethod
    @property
    def update_document(cls):
        """Wiki Documents should be merged/updated."""
        return True

    @classmethod
    def prepare(cls, instance):
        """Override super method to merge docs for KB."""
        # Add a discard field in the document if the following conditions are met
        # Wiki document is a redirect
        # Wiki document is archived
        # Wiki document is a template
        if any(
            [
                instance.html.startswith(REDIRECT_HTML),
                instance.is_archived,
                instance.category in [TEMPLATES_CATEGORY, CANNED_RESPONSES_CATEGORY],
            ]
        ):
            instance.es_discard_doc = "unindex_me"

        return super(WikiDocument, cls).prepare(instance, parent_id=instance.parent_id)

    def prepare_updated(self, instance):
        return getattr(instance.current_revision, "created", None)

    def prepare_keywords(self, instance):
        """Return the current revision's keywords as a string."""
        return getattr(instance.current_revision, "keywords", "")

    def prepare_content(self, instance):
        return instance.html

    def prepare_summary(self, instance):
        if instance.current_revision:
            return instance.summary
        return ""

    def prepare_doc_id(self, instance):
        return instance.pk

    def prepare_topic_ids(self, instance):
        return [topic.id for topic in instance.topics.all()]

    def prepare_product_ids(self, instance):
        return [product.id for product in instance.products.all()]

    def prepare_display_order(self, instance):
        return instance.original.display_order

    @classmethod
    def get_model(cls):
        return wiki_models.Document

    @classmethod
    def get_queryset(cls):
        return (
            # do not include any documents without an approved revision
            wiki_models.Document.objects.exclude(current_revision__isnull=True)
            # all documents will need their current revision:
            .select_related("current_revision")
            # parent documents will need their topics and products:
            .prefetch_related("topics", "products")
        )


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
        pass

    @classmethod
    def prepare(cls, instance):
        """Override super method to exclude certain docs."""
        # Add a discard field in the document if the following conditions are met
        # Question document is spam
        if instance.is_spam:
            instance.es_discard_doc = "unindex_me"

        return super(QuestionDocument, cls).prepare(instance)

    def prepare_question_tag_ids(self, instance):
        return [tag.id for tag in instance.tags.all()]

    def prepare_question_has_solution(self, instance):
        return instance.solution_id is not None

    def prepare_question_num_votes(self, instance):
        if hasattr(instance, "es_question_num_votes"):
            return instance.es_question_num_votes
        return instance.num_votes

    def prepare_answer_content(self, instance):
        return [
            answer.content
            for answer in (
                # when bulk indexing use answer queryset prefetched in `get_queryset` method
                # this is to avoid running an extra query for each question in the chunk
                instance.es_question_answers_not_spam
                if hasattr(instance, "es_question_answers_not_spam")
                # fallback if non-spam answers haven't been prefetched
                else instance.answers.filter(is_spam=False)
            )
        ]

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
            Question.objects
            # prefetch answers which aren't spam to avoid extra queries when iterating over them
            .prefetch_related(
                Prefetch(
                    "answers",
                    queryset=Answer.objects.filter(is_spam=False),
                    to_attr="es_question_answers_not_spam",
                )
            )
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

    num_helpful_votes = field.Integer()
    num_unhelpful_votes = field.Integer()

    is_solution = field.Boolean()

    @classmethod
    def prepare(cls, instance, **kwargs):
        """Override super method to exclude certain docs."""
        # Add a discard field in the document if the following conditions are met
        # Answer document is spam
        if instance.is_spam or instance.question.is_spam:
            instance.es_discard_doc = "unindex_me"

        obj = super().prepare(instance, **kwargs)
        # add a prefix to the id so we don't clash with QuestionDocuments
        obj.meta.id = "a_{}".format(obj.meta.id)
        return obj

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

    def to_action(self, *args, **kwargs):
        # if the id is un-prefixed, add it
        if not str(self.meta.id).startswith("a_"):
            self.meta.id = f"a_{self.meta.id}"
        return super().to_action(*args, **kwargs)

    @classmethod
    def get(cls, id, **kwargs):
        # if the id is un-prefixed, add it
        if not str(id).startswith("a_"):
            id = f"a_{id}"
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
        pass

    @classmethod
    def prepare(cls, instance):
        """Override super method to exclude docs from indexing."""
        # Add a discard field in the document if the following conditions are met
        # User is not active
        if not instance.user.is_active:
            instance.es_discard_doc = "unindex_me"

        return super(ProfileDocument, cls).prepare(instance)

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
    forum_slug = field.Keyword()
    thread_id = field.Keyword()
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
        pass

    def prepare_forum_slug(self, instance):
        return instance.thread.forum.slug

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
        return Post.objects.prefetch_related("thread", "thread__forum")
