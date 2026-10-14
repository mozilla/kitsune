import json
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from kitsune.llm.categorization.classifiers import (
    classify_product,
    classify_topic,
    eligible_products,
)
from kitsune.llm.tests import choice_answer
from kitsune.llm.utils import DecisionError
from kitsune.products.models import Product, ProductSupportConfig, Topic
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    SupportOrganizationFactory,
    TopicFactory,
    ZendeskConfigFactory,
)
from kitsune.questions.tests import AAQConfigFactory, QuestionLocaleFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import GroupFactory, UserFactory


@override_settings(PRODUCT_REASSIGN_PROBABILITY=0.90, MOZILLA_ACCOUNT_REASSIGN_PROBABILITY=0.95)
class ProductClassificationTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.locale = QuestionLocaleFactory(locale="en-US")
        self.forum = AAQConfigFactory(enabled_locales=[self.locale])
        self.current = self.product(title="Firefox", slug="firefox")
        self.target = self.product(title="Firefox for Android", slug="firefox-android")
        self.payload = {
            "subject": "Firefox for Android tabs disappear",
            "content": "The Android tab tray closes all my tabs.",
            "product": self.current,
            "channel": "forum",
            "locale": "en-US",
            "user": self.user,
        }
        patcher = patch("kitsune.llm.categorization.classifiers.evaluate_decisions")
        self.evaluate = patcher.start()
        self.addCleanup(patcher.stop)

    def product(self, *, ticket=False, active=True, **kwargs):
        product = ProductFactory(**kwargs)
        ProductSupportConfigFactory(
            product=product,
            is_active=active,
            forum_config=None if ticket else self.forum,
            zendesk_config=ZendeskConfigFactory() if ticket else None,
        )
        return product

    def classify(self, value, probability):
        self.evaluate.return_value = choice_answer("product", value, probability)
        return classify_product(self.payload)["product_result"]

    def test_reassignment_uses_option_probability_at_boundary(self):
        for probability, reassigned in [(0.51, False), (0.8999, False), (0.90, True), (1, True)]:
            with self.subTest(probability=probability):
                result = self.classify(f"product:{self.target.pk}", probability)
                self.assertEqual(result["reassigned"], reassigned)
                self.assertEqual(
                    result["product_id"], self.target.pk if reassigned else self.current.pk
                )
                self.assertEqual(result["predicted_product_id"], self.target.pk)
                self.assertEqual(result["probability"], probability)

    def test_reassignment_cutoff_is_read_at_call_time(self):
        with self.settings(PRODUCT_REASSIGN_PROBABILITY=0.98):
            result = self.classify(f"product:{self.target.pk}", 0.97)
            self.assertFalse(result["reassigned"])
        self.assertTrue(self.classify(f"product:{self.target.pk}", 0.97)["reassigned"])

    def test_invalid_reassignment_cutoffs_cannot_authorize_moves(self):
        for name in ("PRODUCT_REASSIGN_PROBABILITY", "MOZILLA_ACCOUNT_REASSIGN_PROBABILITY"):
            for cutoff in (True, "0.99", -0.1, 1.1, float("nan"), float("inf")):
                with self.subTest(name=name, cutoff=cutoff), self.settings(**{name: cutoff}):
                    with self.assertRaises(ImproperlyConfigured):
                        self.classify(f"product:{self.target.pk}", 0.99)

    def test_accounts_source_requires_stricter_probability(self):
        accounts = self.product(title="Mozilla Accounts", slug="mozilla-account", visible=False)
        self.payload["product"] = accounts
        for probability, reassigned in [(0.90, False), (0.9499, False), (0.95, True)]:
            with self.subTest(probability=probability):
                result = self.classify(f"product:{self.target.pk}", probability)
                self.assertEqual(result["reassigned"], reassigned)
                self.assertEqual(
                    result["product_id"], self.target.pk if reassigned else accounts.pk
                )
        with self.settings(MOZILLA_ACCOUNT_REASSIGN_PROBABILITY=0.99):
            result = self.classify(f"product:{self.target.pk}", 0.98)
            self.assertFalse(result["reassigned"])

    def test_same_product_and_unknown_retain_current(self):
        result = self.classify(f"product:{self.current.pk}", 0.99)
        self.assertEqual(result["product_id"], self.current.pk)
        self.assertEqual(result["predicted_product_id"], self.current.pk)
        self.assertFalse(result["reassigned"])
        result = self.classify("unknown", 0.99)
        self.assertEqual(result["product_id"], self.current.pk)
        self.assertIsNone(result["predicted_product_id"])
        self.assertFalse(result["reassigned"])

    def test_product_ids_disambiguate_duplicate_titles(self):
        Product.objects.filter(pk=self.target.pk).update(title=self.current.title)
        result = self.classify(f"product:{self.target.pk}", 0.99)
        self.assertEqual(result["product_id"], self.target.pk)
        self.assertTrue(result["reassigned"])

    def test_product_can_be_selected_without_a_current_product(self):
        self.payload.pop("product")
        for probability, expected_id in [(0.8999, None), (0.90, self.target.pk)]:
            with self.subTest(probability=probability):
                result = self.classify(f"product:{self.target.pk}", probability)
                self.assertEqual(result["product_id"], expected_id)
                self.assertEqual(result["reassigned"], expected_id is not None)
        result = self.classify("unknown", 1)
        self.assertIsNone(result["product_id"])
        self.assertFalse(result["reassigned"])

    def test_catalog_tracks_added_and_archived_products_without_a_business_cap(self):
        self.assertCountEqual(eligible_products(self.payload), [self.current, self.target])
        added = [self.product(title=f"Added product {index}") for index in range(19)]
        target = added[-1]
        result = self.classify(f"product:{target.pk}", 0.99)
        self.assertEqual(result["product_id"], target.pk)
        self.assertTrue(result["reassigned"])
        choices = self.evaluate.call_args.args[1][0]["choices"]
        self.assertCountEqual(
            [choice["value"] for choice in choices],
            [
                *(f"product:{product.pk}" for product in [self.current, self.target, *added]),
                "unknown",
            ],
        )
        target.is_archived = True
        target.save()
        result = self.classify(f"product:{target.pk}", 0.99)
        self.assertEqual(result["product_id"], self.current.pk)
        self.assertFalse(result["reassigned"])
        self.assertIsNone(result["probability"])
        self.assertNotIn(target, eligible_products(self.payload))

    def test_forum_catalog_respects_locale_visibility_and_activity(self):
        self.product(title="Hidden", visible=False)
        self.product(title="Archived", is_archived=True)
        self.product(title="Inactive support", active=False)
        self.product(title="Tickets only", ticket=True)
        other_locale = self.product(title="French only")
        config = other_locale.support_configs.get()
        config.forum_config = AAQConfigFactory(
            enabled_locales=[QuestionLocaleFactory(locale="fr")]
        )
        config.save()
        accounts = self.product(title="Mozilla Accounts", slug="mozilla-account", visible=False)
        self.assertCountEqual(
            [p.pk for p in eligible_products(self.payload)],
            [self.current.pk, self.target.pk, accounts.pk],
        )
        result = self.classify(f"product:{other_locale.pk}", 1)
        self.assertFalse(result["reassigned"])
        self.assertIsNone(result["probability"])

    def test_ticket_channel_never_offers_forum_only_destinations(self):
        ticket_product = self.product(title="VPN", ticket=True)
        self.product(title="Inactive ticket support", ticket=True, active=False)
        self.payload["channel"] = "ticket"
        self.assertEqual([p.pk for p in eligible_products(self.payload)], [ticket_product.pk])
        result = self.classify(f"product:{self.target.pk}", 1)
        self.assertFalse(result["reassigned"])
        self.assertIsNone(result["probability"])
        result = self.classify(f"product:{ticket_product.pk}", 0.99)
        self.assertEqual(result["product_id"], ticket_product.pk)

    def test_subscription_required_before_destination_is_eligible(self):
        target = self.product(title="Subscription product", ticket=True)
        config = target.support_configs.get()
        config.subscription_only = True
        config.save()
        self.payload["channel"] = "ticket"
        self.assertEqual(eligible_products(self.payload), [])
        self.user.profile.products.add(target)
        self.assertEqual([p.pk for p in eligible_products(self.payload)], [target.pk])

    def test_organization_channel_policy_is_preserved(self):
        config = self.target.support_configs.get()
        config.zendesk_config = ZendeskConfigFactory()
        config.default_support_type = ProductSupportConfig.SUPPORT_TYPE_FORUM
        config.save()
        group = GroupFactory()
        SupportOrganizationFactory(config=config, group=group)
        self.payload["channel"] = "ticket"
        self.assertEqual(eligible_products(self.payload), [])
        self.user.groups.add(group)
        self.assertEqual([p.pk for p in eligible_products(self.payload)], [self.target.pk])

    def test_user_and_group_details_are_not_sent_to_provider(self):
        self.user.groups.add(GroupFactory(name="private-classification-group"))
        self.classify(f"product:{self.current.pk}", 1)
        sent = json.loads(self.evaluate.call_args.args[0])
        self.assertNotIn("user", sent)
        self.assertNotIn("groups", sent)
        self.assertNotIn(self.user.email, self.evaluate.call_args.args[0])
        self.assertNotIn("private-classification-group", self.evaluate.call_args.args[0])

    def test_malformed_product_metadata_does_not_break_classification(self):
        Product.objects.filter(pk=self.target.pk).update(metadata=["legacy value"])
        result = self.classify(f"product:{self.target.pk}", 0.99)
        self.assertTrue(result["reassigned"])
        choices = self.evaluate.call_args.args[1][0]["choices"]
        target_choice = next(
            choice for choice in choices if choice["value"] == f"product:{self.target.pk}"
        )
        self.assertEqual(
            json.loads(target_choice["description"])["description"], self.target.description
        )

    def test_empty_or_unscoped_catalog_skips_provider(self):
        for changes in [{"locale": "fr"}, {"locale": None}, {"channel": "unknown"}]:
            with self.subTest(changes=changes):
                result = classify_product({**self.payload, **changes})["product_result"]
                self.assertEqual(result["product_id"], self.current.pk)
                self.assertIsNone(result["probability"])
                self.assertFalse(result["reassigned"])
        self.evaluate.assert_not_called()

    def test_service_error_refusal_and_bad_probabilities_abstain(self):
        self.evaluate.side_effect = DecisionError("service unavailable")
        result = classify_product(self.payload)["product_result"]
        self.assertFalse(result["reassigned"])
        self.assertIsNone(result["probability"])
        self.evaluate.side_effect = None
        value = f"product:{self.target.pk}"
        invalid_answers = [
            {},
            {"product": {"type": "refusal", "name": "product"}},
            choice_answer("product", "not-supplied", 1),
            choice_answer("product", value, None),
            choice_answer("product", value, "0.99"),
            choice_answer("product", value, True),
            choice_answer("product", value, float("nan")),
            choice_answer("product", value, float("inf")),
            choice_answer("product", value, -0.1),
            choice_answer("product", value, 1.1),
            {"product": {"type": "choice", "choice": value, "probabilities": []}},
        ]
        for answer in invalid_answers:
            with self.subTest(answer=answer):
                self.evaluate.return_value = answer
                result = classify_product(self.payload)["product_result"]
                self.assertEqual(result["product_id"], self.current.pk)
                self.assertIsNone(result["predicted_product_id"])
                self.assertIsNone(result["probability"])
                self.assertFalse(result["reassigned"])

    def test_missing_or_duplicate_selected_probability_abstains(self):
        value = f"product:{self.target.pk}"
        for probabilities in [
            [{"value": "unknown", "probability": 1}],
            [{"value": value, "probability": 0.99}, {"value": value, "probability": 0.01}],
            [
                {"value": value, "probability": 0.99},
                {"value": "not-supplied", "probability": 0.01},
            ],
        ]:
            with self.subTest(probabilities=probabilities):
                answer = choice_answer("product", value, 0.99)
                answer["product"]["probabilities"] = probabilities
                self.evaluate.return_value = answer
                result = classify_product(self.payload)["product_result"]
                self.assertFalse(result["reassigned"])
                self.assertIsNone(result["probability"])

    @override_settings(DECISIONS_MAX_CHOICES=3)
    def test_catalog_limit_includes_unknown_choice(self):
        result = self.classify(f"product:{self.target.pk}", 0.99)
        self.assertTrue(result["reassigned"])
        self.product(title="One too many")
        self.evaluate.reset_mock()
        result = classify_product(self.payload)["product_result"]
        self.assertEqual(result["product_id"], self.current.pk)
        self.assertFalse(result["reassigned"])
        self.assertIsNone(result["probability"])
        self.evaluate.assert_not_called()


class TopicClassificationTests(TestCase):
    def setUp(self):
        self.product = ProductFactory(title="Firefox")
        self.topic = TopicFactory(
            title="Settings",
            products=[self.product],
            metadata={"description": "Browser settings", "examples": ["Change my settings"]},
        )
        self.payload = {
            "subject": "Change my browser settings",
            "content": "How do I change my settings?",
            "product": self.product,
            "channel": "forum",
            "locale": "en-US",
        }
        patcher = patch("kitsune.llm.categorization.classifiers.evaluate_decisions")
        self.evaluate = patcher.start()
        self.addCleanup(patcher.stop)

    def test_duplicate_titles_keep_topic_identity(self):
        other_parent = TopicFactory(
            title="Privacy", products=[self.product], metadata={"description": "Privacy"}
        )
        TopicFactory(
            title="Preferences",
            parent=self.topic,
            products=[self.product],
            metadata={"description": "General preferences", "examples": ["Change home page"]},
        )
        other_child = TopicFactory(
            title="Preferences",
            parent=other_parent,
            products=[self.product],
            metadata={"description": "Privacy preferences", "examples": ["Block tracking"]},
        )
        self.payload["selected_topic"] = self.topic.title
        self.evaluate.return_value = choice_answer("topic", f"topic:{other_child.pk}", 0.8)
        result = classify_topic(self.payload)["topic_result"]
        self.assertEqual(result["topic_id"], other_child.pk)
        self.assertEqual(result["probability"], 0.8)

    def test_taxonomy_excludes_other_products_hidden_archived_and_missing_metadata(self):
        excluded = [
            TopicFactory(products=[ProductFactory()], metadata={"description": "Other product"}),
            TopicFactory(
                products=[self.product], visible=False, metadata={"description": "Hidden"}
            ),
            TopicFactory(
                products=[self.product], is_archived=True, metadata={"description": "Archived"}
            ),
            TopicFactory(products=[self.product], metadata={}),
        ]
        excluded += [
            TopicFactory(
                products=[self.product],
                parent=parent,
                metadata={"description": "Child of an ineligible parent"},
            )
            for parent in excluded
        ]
        for topic in excluded:
            with self.subTest(topic=topic.pk):
                self.evaluate.return_value = choice_answer("topic", f"topic:{topic.pk}", 1)
                result = classify_topic(self.payload)["topic_result"]
                self.assertIsNone(result["topic_id"])
                self.assertIsNone(result["probability"])
        self.evaluate.return_value = choice_answer("topic", f"topic:{self.topic.pk}", 0.8)
        self.assertEqual(classify_topic(self.payload)["topic_result"]["topic_id"], self.topic.pk)

    def test_undefined_and_empty_taxonomy(self):
        self.evaluate.return_value = choice_answer("topic", "undefined", 0.85)
        result = classify_topic(self.payload)["topic_result"]
        self.assertIsNone(result["topic_id"])
        self.assertEqual(result["probability"], 0.85)
        for metadata in ({}, ["legacy value"]):
            with self.subTest(metadata=metadata):
                Topic.objects.filter(pk=self.topic.pk).update(metadata=metadata)
                self.evaluate.reset_mock()
                result = classify_topic(self.payload)["topic_result"]
                self.assertIsNone(result["topic_id"])
                self.assertIsNone(result["probability"])
                self.evaluate.assert_not_called()

    def test_service_failure_and_refusal_abstain(self):
        self.evaluate.side_effect = DecisionError("service unavailable")
        result = classify_topic(self.payload)["topic_result"]
        self.assertIsNone(result["topic_id"])
        self.assertIsNone(result["probability"])
        self.evaluate.side_effect = None
        self.evaluate.return_value = {"topic": {"type": "refusal", "name": "topic"}}
        result = classify_topic(self.payload)["topic_result"]
        self.assertIsNone(result["topic_id"])
        self.assertIsNone(result["probability"])

    @override_settings(DECISIONS_MAX_CHOICES=2)
    def test_catalog_limit_includes_undefined_choice(self):
        self.evaluate.return_value = choice_answer("topic", f"topic:{self.topic.pk}", 0.9)
        result = classify_topic(self.payload)["topic_result"]
        self.assertEqual(result["topic_id"], self.topic.pk)
        TopicFactory(products=[self.product], metadata={"description": "One too many"})
        self.evaluate.reset_mock()
        result = classify_topic(self.payload)["topic_result"]
        self.assertIsNone(result["topic_id"])
        self.assertIsNone(result["probability"])
        self.evaluate.assert_not_called()
