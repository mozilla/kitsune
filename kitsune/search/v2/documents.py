from elasticsearch_dsl import Document as DSLDocument
from elasticsearch_dsl import connections, field
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


class QuestionDocument(DSLDocument):
    """
    """

    question_id = field.Integer()
    question_title = field.Keyword(fields={"text": field.Text()})
    question_content = field.Object(
        properties={
            "en-US": field.Text(analyzer="english"),
            "cs": field.Text(analyzer="czech"),
            "hu": field.Text(analyzer="hungarian"),
        }
    )

    locale = field.Keyword()

    class Index:
        name = config.QUESTION_INDEX_NAME
        using = config.DEFAULT_ES7_CONNECTION

    @classmethod
    def prepare_locale(cls, instance):
        return cls.get_question_instance(instance).locale

    @classmethod
    def prepare(cls, instance):
        """Prepare an object given a model instance"""

        fields = ["question_id", "question_title", "question_content", "locale"] + cls.get_fields()
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

    @classmethod
    def get_fields(cls):
        return ["content"]

    @classmethod
    def get_question_instance(cls, instance):
        return instance.question

    @classmethod
    def get_model(cls):
        return question_models.Answer
