from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from parameterized import parameterized

from kitsune.products.models import CuratedBlock, CuratedBlockItem, ProductSupportConfig
from kitsune.products.tests import (
    CuratedBlockFactory,
    CuratedBlockItemFactory,
    ProductFactory,
    ProductSupportConfigFactory,
    TopicFactory,
    ZendeskConfigFactory,
    make_article,
)
from kitsune.questions.tests import AAQConfigFactory, QuestionFactory, QuestionLocaleFactory
from kitsune.sumo.tests import TestCase
from kitsune.wiki.tests import RedirectRevisionFactory


class TopicModelTests(TestCase):
    def test_path(self):
        """Verify that the path property works."""
        p = ProductFactory(slug="p")
        t1 = TopicFactory(products=[p], slug="t1")
        t2 = TopicFactory(products=[p], slug="t2", parent=t1)
        t3 = TopicFactory(products=[p], slug="t3", parent=t2)

        self.assertEqual(t1.path, [t1.slug])
        self.assertEqual(t2.path, [t1.slug, t2.slug])
        self.assertEqual(t3.path, [t1.slug, t2.slug, t3.slug])

    def test_absolute_url(self):
        p = ProductFactory()
        t = TopicFactory(products=[p])
        expected = f"/en-US/products/{p.slug}/{t.slug}"
        actual = t.get_absolute_url(p.slug)
        self.assertEqual(actual, expected)

    def test_absolute_url_subtopic(self):
        p = ProductFactory()
        t1 = TopicFactory(products=[p])
        t2 = TopicFactory(parent=t1, products=[p])
        expected = f"/en-US/products/{p.slug}/{t1.slug}/{t2.slug}"
        actual = t2.get_absolute_url(p.slug)
        self.assertEqual(actual, expected)

    def test_absolute_url_topics(self):
        t = TopicFactory()
        expected = f"/en-US/topics/{t.slug}"
        actual = t.get_absolute_url()
        self.assertEqual(actual, expected)


class ProductModelTests(TestCase):
    def test_absolute_url(self):
        p = ProductFactory()
        expected = "/en-US/products/{p}".format(p=p.slug)
        actual = p.get_absolute_url()
        self.assertEqual(actual, expected)


class ProductSupportConfigCleanTests(TestCase):
    def test_forum_config_with_no_locales_raises(self):
        """Active config with forum_config that has no enabled locales should fail."""
        aaq_config = AAQConfigFactory()
        product = ProductFactory()
        psc = ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            is_active=True,
        )
        with self.assertRaises(ValidationError):
            psc.clean()

    def test_forum_config_with_locales_passes(self):
        """Active config with forum_config that has enabled locales should pass."""
        locale = QuestionLocaleFactory(locale="en-US")
        aaq_config = AAQConfigFactory(enabled_locales=[locale])
        product = ProductFactory()
        psc = ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            is_active=True,
        )
        psc.clean()  # Should not raise

    def test_active_with_zendesk_only_passes(self):
        """Active config with only zendesk_config should pass."""
        zendesk_config = ZendeskConfigFactory()
        product = ProductFactory()
        psc = ProductSupportConfigFactory(
            product=product,
            zendesk_config=zendesk_config,
            is_active=True,
        )
        psc.clean()  # Should not raise

    def test_active_with_both_channels_passes(self):
        """Active config with both channels should pass."""
        locale = QuestionLocaleFactory(locale="en-US")
        aaq_config = AAQConfigFactory(enabled_locales=[locale])
        zendesk_config = ZendeskConfigFactory()
        product = ProductFactory()
        psc = ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            is_active=True,
        )
        psc.clean()  # Should not raise

    def test_inactive_skips_validation(self):
        """Inactive config skips all validation."""
        aaq_config = AAQConfigFactory()
        zendesk_config = ZendeskConfigFactory()
        product = ProductFactory()
        psc = ProductSupportConfigFactory(
            product=product,
            forum_config=aaq_config,
            zendesk_config=zendesk_config,
            is_active=False,
        )
        psc.clean()  # Should not raise even though forum_config has no locales

    def test_active_with_no_channels_raises(self):
        """Active config with no support channels should fail validation."""
        product = ProductFactory()
        psc = ProductSupportConfig(product=product, is_active=True)
        with self.assertRaises(ValidationError):
            psc.clean()

    def test_save_with_no_channels_raises_integrity_error(self):
        """Saving with no support channels should fail due to DB constraint."""
        product = ProductFactory()
        with self.assertRaises(IntegrityError):
            ProductSupportConfigFactory(
                product=product,
                forum_config=None,
                zendesk_config=None,
            )


Kind = CuratedBlock.Kind
Variant = CuratedBlock.Variant


class CuratedBlockCleanTests(TestCase):
    def setUp(self):
        self.product = ProductFactory()
        self.topic = TopicFactory(products=[self.product])

    def build(self, **kwargs):
        return CuratedBlockFactory.build(
            **{"product": self.product, "topic": self.topic, **kwargs}
        )

    @parameterized.expand(
        [
            (Kind.CALLOUT, Variant.NUMBERED),
            (Kind.CALLOUT, Variant.MANUAL),
            (Kind.ARTICLES, Variant.IMPORTANT),
            (Kind.QUESTIONS, Variant.FEATURED),
        ]
    )
    def test_variant_must_match_kind(self, kind, variant):
        with self.assertRaises(ValidationError) as cm:
            self.build(kind=kind, variant=variant).clean()

        self.assertEqual({"variant"}, set(cm.exception.message_dict))

    @parameterized.expand(
        [
            (Kind.CALLOUT, Variant.GOOD_TO_KNOW, ""),
            (Kind.CALLOUT, Variant.IMPORTANT, "   "),
            (Kind.ARTICLES, Variant.NUMBERED, "Hello"),
            (Kind.QUESTIONS, Variant.MANUAL, "Hello"),
            (Kind.QUESTIONS, Variant.AUTOMATIC, "Hello"),
        ]
    )
    def test_message_only_on_callouts_and_required_for_them(self, kind, variant, message):
        with self.assertRaises(ValidationError) as cm:
            self.build(kind=kind, variant=variant, message=message).clean()

        self.assertEqual({"message"}, set(cm.exception.message_dict))

    @parameterized.expand(
        [
            ("triple_quotes", 'Say """hi"""'),
            ("backslash", "C:\\temp"),
            ("trailing_quote", 'Press "OK"'),
        ]
    )
    def test_message_must_survive_string_extraction(self, _name, message):
        with self.assertRaises(ValidationError) as cm:
            self.build(message=message).clean()

        self.assertEqual({"message"}, set(cm.exception.message_dict))

    def test_topic_must_belong_to_product(self):
        other_topic = TopicFactory(products=[ProductFactory()])

        with self.assertRaises(ValidationError) as cm:
            self.build(topic=other_topic).clean()

        self.assertEqual({"topic"}, set(cm.exception.message_dict))

    def test_clean_skips_checks_for_missing_fields(self):
        block = CuratedBlock(kind="", variant="", message="Hello")

        block.clean()


INELIGIBLE_ARTICLES = [
    ("other_product", lambda product: make_article(ProductFactory())),
    (
        "restricted",
        lambda product: make_article(
            product, restrict_to_groups=[Group.objects.create(name="restricted")]
        ),
    ),
    ("redirect", lambda product: RedirectRevisionFactory(document__products=[product]).document),
    ("not_english", lambda product: make_article(product, locale="de")),
]


class CuratedBlockCleanItemsTests(TestCase):
    def setUp(self):
        self.product = ProductFactory()
        self.topic = TopicFactory(products=[self.product])

    def build(self, kind, variant):
        return CuratedBlockFactory.build(
            product=self.product, topic=self.topic, kind=kind, variant=variant
        )

    def items(self, kind, count):
        if kind == Kind.QUESTIONS:
            return [
                CuratedBlockItem(position=i, question=QuestionFactory(product=self.product))
                for i in range(count)
            ]
        return [
            CuratedBlockItem(position=i, document=make_article(self.product)) for i in range(count)
        ]

    @parameterized.expand(
        [
            ("callout_empty", Kind.CALLOUT, Variant.GOOD_TO_KNOW, 0, True),
            ("callout_max", Kind.CALLOUT, Variant.IMPORTANT, 3, True),
            ("callout_over", Kind.CALLOUT, Variant.IMPORTANT, 4, False),
            ("articles_under", Kind.ARTICLES, Variant.NUMBERED, 1, False),
            ("articles_min", Kind.ARTICLES, Variant.NUMBERED, 2, True),
            ("articles_max", Kind.ARTICLES, Variant.FEATURED, 6, True),
            ("articles_over", Kind.ARTICLES, Variant.FEATURED, 7, False),
            ("manual_under", Kind.QUESTIONS, Variant.MANUAL, 1, False),
            ("manual_min", Kind.QUESTIONS, Variant.MANUAL, 2, True),
            ("manual_max", Kind.QUESTIONS, Variant.MANUAL, 4, True),
            ("manual_over", Kind.QUESTIONS, Variant.MANUAL, 5, False),
            ("automatic_empty", Kind.QUESTIONS, Variant.AUTOMATIC, 0, True),
            ("automatic_with_item", Kind.QUESTIONS, Variant.AUTOMATIC, 1, False),
        ]
    )
    def test_item_counts(self, _name, kind, variant, count, is_valid):
        block = self.build(kind, variant)
        items = self.items(kind, count)

        if is_valid:
            block.clean_items(items)
        else:
            with self.assertRaises(ValidationError):
                block.clean_items(items)

    @parameterized.expand(
        [
            ("question_in_callout", Kind.CALLOUT, Variant.IMPORTANT, "question"),
            ("question_in_articles", Kind.ARTICLES, Variant.NUMBERED, "question"),
            ("article_in_manual_questions", Kind.QUESTIONS, Variant.MANUAL, "document"),
            ("empty_item", Kind.CALLOUT, Variant.IMPORTANT, None),
        ]
    )
    def test_items_must_match_the_kind(self, _name, kind, variant, wrong):
        block = self.build(kind, variant)
        items = self.items(kind, 2)
        if wrong == "question":
            items.append(CuratedBlockItem(question=QuestionFactory(product=self.product)))
        elif wrong == "document":
            items.append(CuratedBlockItem(document=make_article(self.product)))
        else:
            items.append(CuratedBlockItem())

        with self.assertRaises(ValidationError):
            block.clean_items(items)

    @parameterized.expand(INELIGIBLE_ARTICLES)
    def test_ineligible_articles_are_rejected(self, _name, make_ineligible):
        article = make_ineligible(self.product)
        block = self.build(Kind.CALLOUT, Variant.GOOD_TO_KNOW)

        with self.assertRaises(ValidationError) as cm:
            block.clean_items([CuratedBlockItem(document=article)])

        self.assertTrue(any(article.title in message for message in cm.exception.messages))

    @parameterized.expand(
        [
            ("spam", {"is_spam": True}),
            ("archived", {"is_archived": True}),
            ("other_product", {"product": "other"}),
            ("no_product", {"product": None}),
        ]
    )
    def test_ineligible_questions_are_rejected(self, _name, fields):
        if fields.get("product") == "other":
            fields = {"product": ProductFactory()}
        bad = QuestionFactory(**{"product": self.product, **fields})
        items = [*self.items(Kind.QUESTIONS, 1), CuratedBlockItem(question=bad)]

        with self.assertRaises(ValidationError) as cm:
            self.build(Kind.QUESTIONS, Variant.MANUAL).clean_items(items)

        self.assertTrue(any(bad.title in message for message in cm.exception.messages))

    @parameterized.expand(
        [
            ("article", Kind.CALLOUT, Variant.GOOD_TO_KNOW),
            ("question", Kind.QUESTIONS, Variant.MANUAL),
        ]
    )
    def test_duplicate_items_are_rejected(self, _name, kind, variant):
        items = self.items(kind, 2)
        items.append(CuratedBlockItem(document=items[0].document, question=items[0].question))

        with self.assertRaises(ValidationError):
            self.build(kind, variant).clean_items(items)


class CuratedBlockItemTests(TestCase):
    def setUp(self):
        self.block = CuratedBlockFactory()

    def test_unique_per_topic_product_and_kind(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            CuratedBlockFactory(product=self.block.product, topic=self.block.topic)

        CuratedBlockFactory(
            product=self.block.product,
            topic=self.block.topic,
            kind=Kind.ARTICLES,
            variant=Variant.NUMBERED,
        )

    def test_exactly_one_of_document_and_question(self):
        document = make_article(self.block.product)
        question = QuestionFactory(product=self.block.product)

        for fields in ({}, {"document": document, "question": question}):
            with self.subTest(fields=sorted(fields)):
                with self.assertRaises(IntegrityError), transaction.atomic():
                    CuratedBlockItemFactory(block=self.block, **fields)

        CuratedBlockItemFactory(block=self.block, document=document)
        CuratedBlockItemFactory(block=self.block, question=question)
