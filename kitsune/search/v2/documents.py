from elasticsearch_dsl import Document as DSLDocument
from elasticsearch_dsl import connections, field, InnerDoc
from kitsune.questions import models as question_models
from kitsune.search import config
from kitsune.search.v2.base import SumoDocument
from kitsune.search.v2.es7_utils import es7_client
from kitsune.search.v2.fields import SumoLocaleAwareTextField
from kitsune.wiki import models as wiki_models
from kitsune.wiki.config import REDIRECT_HTML

connections.add_connection(config.DEFAULT_ES7_CONNECTION, es7_client())


class WikiDocument(SumoDocument):
    url = field.Keyword()
    updated = field.Date()

    product = field.Keyword()
    topic = field.Keyword()

    # Document specific fields (locale aware)
    title = SumoLocaleAwareTextField()
    content = SumoLocaleAwareTextField(store=True, term_vector="with_positions_offsets",)
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


class UserInnerDoc(InnerDoc):
    id = field.Integer()
    username = field.Keyword()


class ProductInnerDoc(InnerDoc):
    id = field.Integer()
    title = field.Keyword()
    slug = field.Keyword()


class TopicInnerDoc(InnerDoc):
    id = field.Integer()
    title = field.Keyword()
    slug = field.Keyword()


class TagInnerDoc(InnerDoc):
    id = field.Integer()
    name = field.Keyword()
    slug = field.Keyword()


class QuestionDocument(DSLDocument):
    """
    """

    question_id = field.Integer()

    question_title = field.Keyword(fields={"text": field.Text()})
    question_creator = field.Object(UserInnerDoc)
    question_content = field.Object(
        properties={
            "en-US": field.Text(analyzer="english"),
            "cs": field.Text(analyzer="czech"),
            "hu": field.Text(analyzer="hungarian"),
        }
    )

    question_updated = field.Date()
    question_updated_by = field.Object(UserInnerDoc)
    question_solution = field.Integer()
    question_is_locked = field.Boolean()
    question_is_archived = field.Boolean()

    question_is_spam = field.Boolean()
    question_marked_as_spam = field.Date()
    question_marked_as_spam_by = field.Object(UserInnerDoc)

    question_product = field.Object(ProductInnerDoc)
    question_topic = field.Object(TopicInnerDoc)

    question_taken_by = field.Object(UserInnerDoc)
    question_taken_until = field.Date()

    question_tags = field.Object(TagInnerDoc)

    locale = field.Keyword()

    class Index:
        name = config.QUESTION_INDEX_NAME
        using = config.DEFAULT_ES7_CONNECTION

    @classmethod
    def prepare_question_creator(cls, instance):
        user = cls.get_question_instance(instance).creator
        return UserInnerDoc(id=user.id, username=user.username)

    @classmethod
    def prepare_question_updated_by(cls, instance):
        user = cls.get_question_instance(instance).updated_by
        return UserInnerDoc(id=user.id, username=user.username)

    @classmethod
    def prepare_question_marked_as_spam_by(cls, instance):
        user = cls.get_question_instance(instance).marked_as_spam_by
        return UserInnerDoc(id=user.id, username=user.username)

    @classmethod
    def prepare_question_taken_by(cls, instance):
        user = cls.get_question_instance(instance).taken_by
        return UserInnerDoc(id=user.id, username=user.username)

    @classmethod
    def prepare_question_solution(cls, instance):
        solution = cls.get_question_instance(instance).solution
        return solution.id if solution else None

    @classmethod
    def prepare_question_product(cls, instance):
        product = cls.get_question_instance(instance).product
        return ProductInnerDoc(id=product.id, title=product.title, slug=product.slug)

    @classmethod
    def prepare_question_topic(cls, instance):
        topic = cls.get_question_instance(instance).topic
        return TopicInnerDoc(id=topic.id, title=topic.title, slug=topic.slug)

    @classmethod
    def prepare_question_tags(cls, instance):
        tags = cls.get_question_instance(instance).tags.all()
        return [TagInnerDoc(id=tag.id, name=tag.name, slug=tag.slug) for tag in tags]

    @classmethod
    def prepare_locale(cls, instance):
        return cls.get_question_instance(instance).locale

    @classmethod
    def prepare(cls, instance):
        """Prepare an object given a model instance"""

        fields = [
            "question_id",
            "question_title",
            "question_creator",
            "question_content",
            "question_updated",
            "question_updated_by",
            "question_solution",
            "question_is_locked",
            "question_is_spam",
            "question_marked_as_spam",
            "question_marked_as_spam_by",
            "question_product",
            "question_topic",
            "question_taken_by",
            "question_taken_until",
            "question_tags",
            "locale",
        ] + cls.get_fields()
        locale_fields = ["question_content"]

        obj = cls()

        # Iterate over fields and either set the value directly from the instance
        # or prepare based on `prepare_<field>` method
        for f in fields:
            try:
                prepare_method = getattr(obj, "prepare_{}".format(f))
                value = prepare_method(instance)
            except AttributeError:
                if f.startswith("question_"):
                    value = getattr(cls.get_question_instance(instance), f[len("question_") :])
                else:
                    value = getattr(instance, f)

            if f in locale_fields:
                setattr(obj, f, {})
                setattr(obj[f], cls.prepare_locale(instance), value)
            else:
                setattr(obj, f, value)

        obj.meta.id = instance.id

        return obj

    @classmethod
    def get_fields(cls):
        return []

    @classmethod
    def get_question_instance(cls, instance):
        return instance

    @classmethod
    def get_model(cls):
        return question_models.Question


class AnswerDocument(QuestionDocument):
    """
    """

    content = field.Text()

    is_solution = field.Boolean()

    @classmethod
    def prepare_is_solution(cls, instance):
        solution = instance.question.solution
        return bool(solution) and solution.id == instance.id

    @classmethod
    def get_fields(cls):
        return ["content", "is_solution"]

    @classmethod
    def get_question_instance(cls, instance):
        return instance.question

    @classmethod
    def get_model(cls):
        return question_models.Answer
