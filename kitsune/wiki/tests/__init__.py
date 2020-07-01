# -*- coding: utf-8 -*-
from datetime import datetime

import factory
from django.conf import settings
from django.template.defaultfilters import slugify
from nose.tools import eq_

from kitsune.products.models import Product
from kitsune.products.tests import ProductFactory
from kitsune.products.tests import TopicFactory
from kitsune.sumo.tests import FuzzyUnicode
from kitsune.sumo.tests import LocalizingClient
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.config import CATEGORIES
from kitsune.wiki.config import REDIRECT_CONTENT
from kitsune.wiki.config import REDIRECT_TITLE
from kitsune.wiki.config import SIGNIFICANCES
from kitsune.wiki.config import TEMPLATE_TITLE_PREFIX
from kitsune.wiki.config import TEMPLATES_CATEGORY
from kitsune.wiki.models import Document
from kitsune.wiki.models import DraftRevision
from kitsune.wiki.models import HelpfulVote
from kitsune.wiki.models import Locale
from kitsune.wiki.models import Revision


class TestCaseBase(TestCase):
    """Base TestCase for the wiki app test cases."""

    client_class = LocalizingClient


class DocumentFactory(factory.DjangoModelFactory):
    class Meta:
        model = Document

    category = CATEGORIES[0][0]
    title = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.title))

    @factory.post_generation
    def products(doc, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            for p in extracted:
                doc.products.add(p)

    @factory.post_generation
    def topics(doc, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            for t in extracted:
                doc.topics.add(t)

    @factory.post_generation
    def tags(doc, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing
            return

        if extracted is not None:
            for t in extracted:
                doc.tags.add(t)


class TemplateDocumentFactory(DocumentFactory):
    category = TEMPLATES_CATEGORY
    title = FuzzyUnicode(prefix=TEMPLATE_TITLE_PREFIX + ":")


class RevisionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Revision

    document = factory.SubFactory(DocumentFactory)
    summary = FuzzyUnicode()
    content = FuzzyUnicode()
    significance = SIGNIFICANCES[0][0]
    comment = FuzzyUnicode()
    creator = factory.SubFactory(UserFactory)
    is_approved = False

    @factory.post_generation
    def set_current_revision(obj, create, extracted, **kwargs):
        if obj.is_approved:
            obj.document.current_revision = obj
            obj.document.save()


class ApprovedRevisionFactory(RevisionFactory):
    is_approved = True
    reviewed = factory.LazyAttribute(lambda o: datetime.now())


class TranslatedRevisionFactory(ApprovedRevisionFactory):
    """Makes a revision that is a translation of an English revision."""

    document = factory.SubFactory(
        DocumentFactory,
        locale=factory.fuzzy.FuzzyChoice(
            loc for loc in settings.SUMO_LANGUAGES if loc != "en-US"
        ),
        parent=factory.SubFactory(
            DocumentFactory, locale=settings.WIKI_DEFAULT_LANGUAGE
        ),
    )
    based_on = factory.SubFactory(
        ApprovedRevisionFactory,
        is_ready_for_localization=True,
        document=factory.SelfAttribute("..document.parent"),
    )


def test_translated_revision_factory():
    rev = TranslatedRevisionFactory()
    assert rev.document.locale != "en-US"
    eq_(rev.based_on.document, rev.document.parent)
    eq_(rev.document.parent.locale, "en-US")


class RedirectRevisionFactory(RevisionFactory):
    class Meta:
        exclude = ("target",)

    target = factory.SubFactory(DocumentFactory)
    document__title = factory.LazyAttribute(
        lambda o: REDIRECT_TITLE
        % {"old": factory.SelfAttribute("..target.title"), "number": 1}
    )
    content = factory.LazyAttribute(lambda o: REDIRECT_CONTENT % o.target.title)
    is_approved = True


class DraftRevisionFactory(factory.DjangoModelFactory):
    class Meta:
        model = DraftRevision

    document = factory.SubFactory(
        DocumentFactory, is_localizable=True, locale=settings.WIKI_DEFAULT_LANGUAGE
    )
    based_on = factory.SubFactory(
        ApprovedRevisionFactory,
        is_ready_for_localization=True,
        document=factory.SelfAttribute("..document"),
    )
    content = FuzzyUnicode()
    creator = factory.SubFactory(UserFactory)
    keywords = "test, test1"
    locale = factory.fuzzy.FuzzyChoice(
        loc for loc in settings.SUMO_LANGUAGES if loc != "en-US"
    )
    summary = FuzzyUnicode()
    title = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.title))


class LocaleFactory(factory.DjangoModelFactory):
    class Meta:
        model = Locale

    locale = "en-US"


class HelpfulVoteFactory(factory.DjangoModelFactory):
    class Meta:
        model = HelpfulVote

    revision = factory.SubFactory(RevisionFactory)


# Todo: This should probably be a non-Django factory class
def new_document_data(topic_ids=None, product_ids=None):
    product_ids = product_ids or [ProductFactory().id]
    p = Product.objects.get(id=product_ids[0])
    topic_ids = topic_ids or [TopicFactory(product=p).id]
    return {
        "title": "A Test Article",
        "slug": "a-test-article",
        "locale": "en-US",
        "topics": topic_ids,
        "products": product_ids,
        "category": CATEGORIES[0][0],
        "keywords": "key1, key2",
        "summary": "lipsum",
        "content": "lorem ipsum dolor sit amet",
    }
