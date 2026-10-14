import json
from unittest.mock import Mock, patch

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase, override_settings
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from kitsune.flagit.models import FlaggedObject
from kitsune.flagit.views import get_flagged_objects
from kitsune.llm.spam.classifier import (
    ModerationAction,
    assess_spam,
    classify_spam,
    determine_action_from_spam_result,
)
from kitsune.llm.tests import decision_answers
from kitsune.llm.utils import DecisionError
from kitsune.products.tests import ProductFactory
from kitsune.questions.models import Question
from kitsune.questions.tests import QuestionFactory
from kitsune.questions.utils import process_classification_result
from kitsune.users.tests import UserFactory

# A genuine question wrongly flagged as spam, from https://github.com/mozilla/sumo/issues/3090.
ISSUE_3090_QUESTION = {
    "subject": "How do I move the weather widget?",
    "content": (
        "On my opening screen the weather widget sits above my shortcuts and I would"
        " like to move it lower down or turn it off. How do I do that?"
    ),
}


@override_settings(
    SPAM_REVIEW_PROBABILITY=0.50,
    SPAM_REJECT_PROBABILITY=0.80,
    SPAM_RELEVANCE_REVIEW_PROBABILITY=0.50,
)
class SpamActionTests(SimpleTestCase):
    def test_probability_boundaries(self):
        for probability, expected in (
            (0, ModerationAction.NOT_SPAM),
            (0.499999, ModerationAction.NOT_SPAM),
            (0.50, ModerationAction.FLAG_REVIEW),
            (0.799999, ModerationAction.FLAG_REVIEW),
            (0.80, ModerationAction.SPAM),
            (1, ModerationAction.SPAM),
        ):
            with self.subTest(probability=probability):
                self.assertEqual(
                    determine_action_from_spam_result(
                        {"probability": probability, "relevance_uncertainty_probability": 0}
                    ),
                    expected,
                )

    def test_relevance_guard_only_prevents_automatic_spam(self):
        for probability, uncertainty, expected in (
            (0.1, 1.0, ModerationAction.NOT_SPAM),
            (0.6, 0.0, ModerationAction.FLAG_REVIEW),
            (0.9, 0.499999, ModerationAction.SPAM),
            (0.9, 0.5, ModerationAction.FLAG_REVIEW),
            (0.9, 1.0, ModerationAction.FLAG_REVIEW),
        ):
            with self.subTest(probability=probability, uncertainty=uncertainty):
                self.assertEqual(
                    determine_action_from_spam_result(
                        {
                            "probability": probability,
                            "relevance_uncertainty_probability": uncertainty,
                        }
                    ),
                    expected,
                )

    def test_settings_overrides_take_effect_without_reimporting(self):
        result = {"probability": 0.7, "relevance_uncertainty_probability": 0.6}
        self.assertEqual(determine_action_from_spam_result(result), ModerationAction.FLAG_REVIEW)
        with override_settings(
            SPAM_REVIEW_PROBABILITY=0.3,
            SPAM_REJECT_PROBABILITY=0.7,
            SPAM_RELEVANCE_REVIEW_PROBABILITY=0.8,
        ):
            self.assertEqual(determine_action_from_spam_result(result), ModerationAction.SPAM)
            result["probability"] = 0.3
            self.assertEqual(
                determine_action_from_spam_result(result), ModerationAction.FLAG_REVIEW
            )
            result["probability"] = 0.299999
            self.assertEqual(determine_action_from_spam_result(result), ModerationAction.NOT_SPAM)
        result["probability"] = 0.7
        self.assertEqual(determine_action_from_spam_result(result), ModerationAction.FLAG_REVIEW)

    def test_missing_or_invalid_probabilities_require_review(self):
        self.assertEqual(determine_action_from_spam_result({}), ModerationAction.FLAG_REVIEW)
        for field in ("probability", "relevance_uncertainty_probability"):
            for value in (None, True, False, "0.1", -0.01, 1.01, float("nan"), float("inf")):
                with self.subTest(field=field, value=value):
                    result = {"probability": 0.1, "relevance_uncertainty_probability": 0.1}
                    result[field] = value
                    self.assertEqual(
                        determine_action_from_spam_result(result), ModerationAction.FLAG_REVIEW
                    )

    def test_invalid_cutoffs_surface_configuration_errors(self):
        for name in (
            "SPAM_REVIEW_PROBABILITY",
            "SPAM_REJECT_PROBABILITY",
            "SPAM_RELEVANCE_REVIEW_PROBABILITY",
        ):
            for value in (None, True, "0.5", -0.01, 1.01, float("nan"), float("inf")):
                with self.subTest(name=name, value=value), override_settings(**{name: value}):
                    with self.assertRaises(ImproperlyConfigured):
                        determine_action_from_spam_result({})

    def test_invalid_cutoff_order_is_not_a_moderation_verdict(self):
        for review, reject in ((0.8, 0.5), (0.5, 0.5)):
            with (
                self.subTest(review=review, reject=reject),
                override_settings(SPAM_REVIEW_PROBABILITY=review, SPAM_REJECT_PROBABILITY=reject),
            ):
                with self.assertRaises(ImproperlyConfigured):
                    determine_action_from_spam_result({})


@override_settings(
    SPAM_REVIEW_PROBABILITY=0.50,
    SPAM_REJECT_PROBABILITY=0.80,
    SPAM_RELEVANCE_REVIEW_PROBABILITY=0.50,
)
class SpamClassifierTests(SimpleTestCase):
    def setUp(self):
        self.products = [
            {
                "title": "Firefox",
                "description": "Mozilla web browser",
                "legitimate_examples": [ISSUE_3090_QUESTION["subject"]],
            },
            {"title": "Mozilla VPN", "description": "Mozilla virtual private network"},
        ]
        self.enterContext(
            patch(
                "kitsune.llm.spam.prompt.get_products",
                return_value=json.dumps({"products": self.products}),
            )
        )
        self.decisions = self.enterContext(
            patch(
                "kitsune.llm.spam.classifier.evaluate_decisions",
                return_value=decision_answers(),
            )
        )
        self.payload = {
            **ISSUE_3090_QUESTION,
            "channel": "forum",
            "locale": "en-US",
            "product": Mock(title="Selected product sentinel"),
        }

    def test_selected_product_and_topic_cannot_change_spam_input(self):
        classify_spam(self.payload)
        first_input = self.decisions.call_args.args[0]
        self.payload["product"] = Mock(title="Different selected product sentinel")
        self.payload["selected_topic"] = "Selected topic sentinel"
        classify_spam(self.payload)
        second_input = self.decisions.call_args.args[0]
        self.assertEqual(first_input, second_input)
        self.assertNotIn("sentinel", second_input)

    def test_missing_malformed_or_refused_decisions_require_review(self):
        for name in ("spam", "relevance_uncertainty"):
            for answer in (
                None,
                {},
                {"type": "refusal", "name": name, "probability": 0},
                {"type": "choice", "name": name, "probability": 0.1},
                {"type": "predicate", "name": "wrong-name", "probability": 0.1},
                {"type": "predicate", "name": name},
                *(
                    {"type": "predicate", "name": name, "probability": value}
                    for value in (None, True, "0.1", -0.1, 1.1, float("nan"), float("inf"))
                ),
            ):
                with self.subTest(name=name, answer=answer):
                    answers = decision_answers()
                    if answer is None:
                        del answers[name]
                    else:
                        answers[name] = answer
                    self.decisions.return_value = answers
                    result = classify_spam(self.payload)["spam_result"]
                    self.assertEqual(
                        determine_action_from_spam_result(result), ModerationAction.FLAG_REVIEW
                    )

    def test_provider_failure_abstains_without_leaking_error_details(self):
        self.decisions.side_effect = DecisionError("private provider detail")
        result = classify_spam(self.payload)["spam_result"]
        self.assertIsNone(result["probability"])
        self.assertIsNone(result["relevance_uncertainty_probability"])
        self.assertEqual(determine_action_from_spam_result(result), ModerationAction.FLAG_REVIEW)
        self.assertNotIn("private provider detail", result["reason"])

    def test_assessment_is_independent_of_decisions_and_product_selection(self):
        assessment = {
            "verdict": "uncertain",
            "spam_signals": [],
            "legitimate_signals": ["A question about browser interface customization."],
            "uncertainty": "The interface cannot be identified from this description alone.",
        }
        messages = []

        def respond(prompt):
            messages.extend(message.content for message in prompt.to_messages())
            return AIMessage(content=json.dumps(assessment))

        payload = {
            **self.payload,
            "spam_result": {"probability": 0.63, "reason": "Prior decision sentinel"},
            "action": "Prior action sentinel",
            "selected_topic": "Selected topic sentinel",
        }
        with patch("kitsune.llm.spam.classifier.get_llm", return_value=RunnableLambda(respond)):
            assess_spam(payload)
        self.assertNotIn("sentinel", "\n".join(messages))
        self.decisions.assert_not_called()

    def test_malformed_assessment_is_not_replaced_with_a_model_verdict(self):
        with patch(
            "kitsune.llm.spam.classifier.get_llm",
            return_value=RunnableLambda(lambda prompt: AIMessage(content='{"verdict": "spam"}')),
        ):
            with self.assertRaises(OutputParserException):
                assess_spam(self.payload)


@override_settings(
    SPAM_REVIEW_PROBABILITY=0.50,
    SPAM_REJECT_PROBABILITY=0.80,
    SPAM_RELEVANCE_REVIEW_PROBABILITY=0.50,
)
class UncertainRelevanceRoutingTests(TestCase):
    """The weather-widget regression must reach a moderator, not automatic spam rejection."""

    def test_uncertain_relevance_reaches_moderators_without_marking_spam(self):
        user = UserFactory()
        product = ProductFactory(title="Firefox", slug="firefox")
        question = QuestionFactory(
            title=ISSUE_3090_QUESTION["subject"],
            content=ISSUE_3090_QUESTION["content"],
            creator=user,
            product=product,
        )
        with patch(
            "kitsune.llm.spam.classifier.evaluate_decisions",
            return_value=decision_answers(0.95, 0.9),
        ):
            result = classify_spam(
                {
                    **ISSUE_3090_QUESTION,
                    "channel": "forum",
                    "locale": question.locale,
                    "user": user,
                }
            )
        process_classification_result(
            question,
            {"action": determine_action_from_spam_result(result["spam_result"]), **result},
        )

        question.refresh_from_db()
        self.assertFalse(question.is_spam)

        flag = FlaggedObject.objects.get(
            content_type=ContentType.objects.get_for_model(Question),
            object_id=question.id,
        )
        self.assertEqual(flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(flag.reason, FlaggedObject.REASON_SPAM)
        pending_for_moderators = get_flagged_objects(
            exclude_reason=FlaggedObject.REASON_CONTENT_MODERATION
        )
        self.assertEqual([flag.object_id for flag in pending_for_moderators], [question.id])

        # Only content-moderation flags should be picked up for automatic reclassification.
        self.assertFalse(
            FlaggedObject.objects.filter(
                status=FlaggedObject.FLAG_PENDING,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
            ).exists()
        )
