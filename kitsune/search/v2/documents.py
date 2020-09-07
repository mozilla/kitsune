from elasticsearch_dsl import connections, field, InnerDoc
from kitsune.search import config
from kitsune.search.v2.base import SumoDocument
from kitsune.search.v2.es7_utils import es7_client
from kitsune.search.v2.fields import SumoLocaleAwareTextField
from kitsune.wiki import models as wiki_models
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.questions import models as question_models
from kitsune.users.models import Profile
from kitsune.forums.models import Thread


connections.add_connection(config.DEFAULT_ES7_CONNECTION, es7_client())


class WikiDocument(SumoDocument):
    url = field.Keyword()
    updated = field.Date()

    product = field.Keyword()
    topic = field.Keyword()

    # Document specific fields (locale aware)
    title = SumoLocaleAwareTextField()
    content = SumoLocaleAwareTextField(store=True, term_vector="with_positions_offsets")
    summary = SumoLocaleAwareTextField(store=True, term_vector="with_positions_offsets")
    keywords = SumoLocaleAwareTextField(multi=True)

    locale = field.Keyword()
    current_id = field.Integer()
    parent_id = field.Integer()
    category = field.Integer()
    slug = field.Keyword()
    is_archived = field.Boolean()
    recent_helpful_votes = field.Integer()
    display_order = field.Integer()

    class Index:
        name = config.WIKI_DOCUMENT_INDEX_NAME
        using = config.DEFAULT_ES7_CONNECTION

    def prepare_url(self, instance):
        return instance.get_absolute_url()

    def prepare_updated(self, instance):
        return getattr(instance.current_revision, "created", None)

    def prepare_product(self, instance):
        return [t.slug for t in instance.get_products()]

    def prepare_topic(self, instance):
        return [t.slug for t in instance.get_topics()]

    def prepare_keywords(self, instance):
        return getattr(instance.current_revision, "keywords", None)

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

    question_tag_id = field.Keyword(multi=True)
    question_num_votes = field.Integer()

    locale = field.Keyword()

    class Index:
        name = config.QUESTION_INDEX_NAME
        using = config.DEFAULT_ES7_CONNECTION

    def prepare_question_tag_id(self, instance):
        return [tag.id for tag in instance.tags.all()]

    def prepare_question_has_solution(self, instance):
        return instance.solution_id is not None

    def get_field_value(self, field, *args):
        if field.startswith("question_"):
            field = field[len("question_") :]
        return super().get_field_value(field, *args)

    @classmethod
    def get_model(cls):
        return question_models.Question


class AnswerDocument(QuestionDocument):
    """
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

    def get_field_value(self, field, instance, *args):
        if field.startswith("question_"):
            instance = instance.question
        return super().get_field_value(field, instance, *args)

    @classmethod
    def get_model(cls):
        return question_models.Answer


class ProductInnerDoc(InnerDoc):
    id = field.Integer()
    title = field.Keyword()
    slug = field.Keyword()

    @classmethod
    def prepare(cls, instance):
        return cls(id=instance.id, title=instance.title, slug=instance.slug)


class GroupInnerDoc(InnerDoc):
    id = field.Integer()
    name = field.Keyword()

    @classmethod
    def prepare(cls, instance):
        return cls(id=instance.id, name=instance.name)


class ProfileDocument(SumoDocument):
    username = field.Keyword(normalizer="lowercase")
    name = field.Text()
    email = field.Keyword()
    # store avatar url so we don't need to hit the db when searching users
    # but set enabled=False to ensure ES does no parsing of it
    avatar = field.Object(enabled=False)

    timezone = field.Keyword()
    country = field.Keyword()
    locale = field.Keyword()

    involved_from = field.Date()

    products = field.Object(ProductInnerDoc)
    groups = field.Object(GroupInnerDoc)

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

    def prepare_products(self, instance):
        return [ProductInnerDoc.prepare(product) for product in instance.products.all()]

    def prepare_groups(self, instance):
        return [GroupInnerDoc.prepare(groups) for groups in instance.user.groups.all()]

    @classmethod
    def get_model(cls):
        return Profile


class PostInnerDoc(InnerDoc):
    content = field.Text()
    author_id = field.Keyword()
    created = field.Date()
    updated = field.Date()
    updated_by_id = field.Keyword()

    @classmethod
    def prepare(cls, instance):
        return cls(
            content=instance.content,
            author_id=instance.author_id,
            created=instance.created,
            updated=instance.updated,
            updated_by_id=instance.updated_by_id if instance.updated_by_id else None,
        )


class ForumThreadDocument(SumoDocument):
    title = field.Text()
    forum_id = field.Keyword()
    created = field.Date()
    creator_id = field.Keyword()
    is_locked = field.Boolean()
    is_sticky = field.Boolean()

    # using Object rather than Nested here for performance at the expense of specificity
    # e.g. we can't search for a thread in which a user jsmith posted "hello world",
    # but we can search for a thread in which "hello world" was posted and jsmith posted
    posts = field.Object(PostInnerDoc, multi=True)

    class Index:
        name = config.FORUM_THREAD_INDEX_NAME
        using = config.DEFAULT_ES7_CONNECTION

    def prepare_posts(self, instance):
        return [PostInnerDoc.prepare(post) for post in instance.post_set.all()]

    @classmethod
    def get_model(cls):
        return Thread
