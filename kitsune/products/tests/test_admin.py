import time

from django.urls import reverse
from parameterized import parameterized

from kitsune.products.models import CuratedBlock
from kitsune.products.tests import (
    CuratedBlockFactory,
    CuratedBlockItemFactory,
    ProductFactory,
    TopicFactory,
    make_article,
)
from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory

Kind = CuratedBlock.Kind
Variant = CuratedBlock.Variant


class CuratedBlockAdminTests(TestCase):
    def setUp(self):
        self.product = ProductFactory()
        self.topic = TopicFactory(products=[self.product])
        self.superuser = UserFactory(is_staff=True, is_superuser=True)
        # Admin requests need an OIDC-backed session with an unexpired ID token.
        self.client.force_login(self.superuser, backend="kitsune.users.auth.SumoOIDCAuthBackend")
        session = self.client.session
        session["oidc_id_token_expiration"] = time.time() + 3600
        session.save()

    def form_data(self, kind, variant, message="", rows=()):
        data = {
            "product": self.product.pk,
            "topic": self.topic.pk,
            "kind": kind,
            "variant": variant,
            "message": message,
            "items-TOTAL_FORMS": len(rows),
            "items-INITIAL_FORMS": sum("id" in row for row in rows),
            "items-MIN_NUM_FORMS": 0,
            "items-MAX_NUM_FORMS": 1000,
        }
        for i, row in enumerate(rows):
            data[f"items-{i}-position"] = i
            data.update({f"items-{i}-{name}": value for name, value in row.items()})
        return data

    @parameterized.expand(
        [
            ("callout", Kind.CALLOUT, Variant.IMPORTANT, "Heads up.", 1, 0),
            ("article_cards", Kind.ARTICLES, Variant.NUMBERED, "", 2, 0),
            ("manual_questions", Kind.QUESTIONS, Variant.MANUAL, "", 0, 2),
        ]
    )
    def test_add_block(self, _name, kind, variant, message, article_count, question_count):
        rows = [{"document": make_article(self.product).pk} for _ in range(article_count)]
        rows += [
            {"question": QuestionFactory(product=self.product).pk} for _ in range(question_count)
        ]

        resp = self.client.post(
            reverse("admin:products_curatedblock_add"),
            self.form_data(kind, variant, message, rows),
        )

        self.assertRedirects(resp, reverse("admin:products_curatedblock_changelist"))
        block = CuratedBlock.objects.get()
        self.assertEqual(block.updated_by, self.superuser)
        self.assertEqual(block.items.count(), len(rows))

    @parameterized.expand(
        [
            (
                "too_few_articles",
                Kind.ARTICLES,
                Variant.NUMBERED,
                lambda test: [{"document": make_article(test.product).pk}],
                "Add between 2 and 6 items (got 1).",
            ),
            (
                "article_of_another_product",
                Kind.CALLOUT,
                Variant.GOOD_TO_KNOW,
                lambda test: [{"document": make_article(ProductFactory()).pk}],
                "must be a published English source article of this product",
            ),
            (
                "article_and_question_in_one_item",
                Kind.CALLOUT,
                Variant.GOOD_TO_KNOW,
                lambda test: [
                    {
                        "document": make_article(test.product).pk,
                        "question": QuestionFactory(product=test.product).pk,
                    }
                ],
                "Choose either an article or a question.",
            ),
            (
                "automatic_with_items",
                Kind.QUESTIONS,
                Variant.AUTOMATIC,
                lambda test: [{"question": QuestionFactory(product=test.product).pk}],
                "Automatic question blocks cannot have items.",
            ),
        ]
    )
    def test_item_validation_errors_show_on_the_form(self, _name, kind, variant, rows, error):
        message = "Heads up." if kind == Kind.CALLOUT else ""

        resp = self.client.post(
            reverse("admin:products_curatedblock_add"),
            self.form_data(kind, variant, message, rows(self)),
        )

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, error)
        self.assertFalse(CuratedBlock.objects.exists())

    def test_switching_to_automatic_can_delete_the_items_in_the_same_save(self):
        editor = UserFactory()
        block = CuratedBlockFactory(
            product=self.product,
            topic=self.topic,
            kind=Kind.QUESTIONS,
            variant=Variant.MANUAL,
            updated_by=editor,
        )
        items = [
            CuratedBlockItemFactory(block=block, question=QuestionFactory(product=self.product))
            for _ in range(2)
        ]
        rows = [
            {"id": item.pk, "block": block.pk, "question": item.question_id, "DELETE": "on"}
            for item in items
        ]

        resp = self.client.post(
            reverse("admin:products_curatedblock_change", args=[block.pk]),
            self.form_data(Kind.QUESTIONS, Variant.AUTOMATIC, rows=rows),
        )

        self.assertRedirects(resp, reverse("admin:products_curatedblock_changelist"))
        block.refresh_from_db()
        self.assertEqual(block.variant, Variant.AUTOMATIC)
        self.assertEqual(block.updated_by, self.superuser)
        self.assertFalse(block.items.exists())

    def test_owner_fields_cannot_be_changed_once_saved(self):
        block = CuratedBlockFactory(product=self.product, topic=self.topic)
        other_topic = TopicFactory(products=[self.product])
        data = {
            **self.form_data(Kind.CALLOUT, Variant.IMPORTANT, "Heads up."),
            "topic": other_topic.pk,
        }

        resp = self.client.post(
            reverse("admin:products_curatedblock_change", args=[block.pk]), data
        )

        self.assertRedirects(resp, reverse("admin:products_curatedblock_changelist"))
        block.refresh_from_db()
        self.assertEqual((block.topic, block.variant), (self.topic, Variant.IMPORTANT))

    @parameterized.expand(
        [
            (
                "document",
                lambda product: make_article(product, title="picker eligible"),
                lambda product: make_article(product, title="picker archived", is_archived=True),
            ),
            (
                "question",
                lambda product: QuestionFactory(product=product, title="picker eligible"),
                lambda product: QuestionFactory(
                    product=product, title="picker spam", is_spam=True
                ),
            ),
        ]
    )
    def test_pickers_only_offer_eligible_items(self, field_name, eligible, ineligible):
        offered = eligible(self.product)
        ineligible(self.product)

        resp = self.client.get(
            reverse("admin:autocomplete"),
            {
                "term": "picker",
                "app_label": "products",
                "model_name": "curatedblockitem",
                "field_name": field_name,
            },
        )

        self.assertEqual([int(result["id"]) for result in resp.json()["results"]], [offered.pk])
