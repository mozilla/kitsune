from unittest.mock import Mock

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import SimpleTestCase, TestCase

from kitsune.flagit.models import FlaggedObject
from kitsune.flagit.views import get_flagged_objects
from kitsune.llm.spam.classifier import (
    HIGH_CONFIDENCE_THRESHOLD,
    LOW_CONFIDENCE_THRESHOLD,
    ModerationAction,
    determine_action_from_spam_result,
)
from kitsune.llm.spam.prompt import UNCERTAIN_RELEVANCE_CONFIDENCE_CEILING, build_spam_prompt
from kitsune.products.models import Product
from kitsune.questions.models import Question
from kitsune.questions.utils import process_classification_result

# A genuine question wrongly flagged as spam, from https://github.com/mozilla/sumo/issues/3090.
ISSUE_3090_QUESTION = {
    "subject": "How do I move the weather widget?",
    "content": (
        "On my opening screen the weather widget sits above my shortcuts and I would"
        " like to move it lower down or turn it off. How do I do that?"
    ),
}


def make_product(title="Firefox", description="", has_ticketing_support=False, metadata=None):
    """Build a stand-in product for prompt rendering, which needs no database."""
    product = Mock()
    product.title = title
    if metadata is None:
        metadata = {"description": description} if description else {}
    product.metadata = metadata
    product.has_ticketing_support = has_ticketing_support
    return product


def render_system_prompt(product, subject="A subject", content="Some content"):
    prompt = build_spam_prompt(product)
    return prompt.format_messages(subject=subject, content=content)[0].content


class SpamPromptRenderingTests(SimpleTestCase):
    """
    Sections are asserted by header only, and the prompt's prose is deliberately left
    untested, so that rewording the guidance does not break the suite.
    """

    def test_product_relevance_section_is_present(self):
        self.assertIn("# Judging product relevance", render_system_prompt(make_product()))

    def test_confidence_ceiling_is_interpolated(self):
        self.assertIn(
            f"must not exceed {UNCERTAIN_RELEVANCE_CONFIDENCE_CEILING}",
            render_system_prompt(make_product()),
        )

    def test_product_description_is_included_only_when_present(self):
        with_description = render_system_prompt(
            make_product(description="Firefox is a free and open-source web browser.")
        )
        self.assertIn("# Product description", with_description)
        self.assertIn("Firefox is a free and open-source web browser.", with_description)

        self.assertNotIn("# Product description", render_system_prompt(make_product()))

    def test_examples_render_as_a_list(self):
        system_prompt = render_system_prompt(
            make_product(
                metadata={
                    "legitimate_examples": [
                        "How do I move the weather widget?",
                        "Why did my wallpaper reset?",
                    ]
                }
            )
        )
        self.assertIn("# Known-legitimate requests", system_prompt)
        self.assertIn("- How do I move the weather widget?", system_prompt)
        self.assertIn("- Why did my wallpaper reset?", system_prompt)

    def test_a_single_string_example_is_accepted(self):
        system_prompt = render_system_prompt(
            make_product(metadata={"legitimate_examples": "Where is the weather widget?"})
        )
        self.assertIn("- Where is the weather widget?", system_prompt)

    def test_no_examples_section_without_usable_values(self):
        for metadata in ({}, {"legitimate_examples": []}, {"legitimate_examples": ["", "  "]}):
            with self.subTest(metadata=metadata):
                self.assertNotIn(
                    "# Known-legitimate requests",
                    render_system_prompt(make_product(metadata=metadata)),
                )

    def test_non_string_items_are_dropped_but_valid_ones_kept(self):
        system_prompt = render_system_prompt(
            make_product(metadata={"legitimate_examples": [None, "Keep me", 42]})
        )
        self.assertIn("- Keep me", system_prompt)
        self.assertNotIn("- 42", system_prompt)
        self.assertNotIn("- None", system_prompt)

    def test_unusable_metadata_is_ignored_rather_than_raising(self):
        for metadata in (
            "not a dict",
            123,
            [],
            None,
            {"legitimate_examples": 42},
            {"legitimate_examples": {"a": "b"}},
            {"legitimate_examples": [None, 42, {"a": "b"}]},
            {"description": 42},
            {"description": None},
        ):
            with self.subTest(metadata=metadata):
                system_prompt = render_system_prompt(make_product(metadata=metadata))
                self.assertNotIn("# Known-legitimate requests", system_prompt)
                self.assertNotIn("# Product description", system_prompt)
                self.assertIn("# What Constitutes Spam?", system_prompt)

    def test_braces_in_metadata_do_not_break_formatting(self):
        """Admin-supplied text is a value, not a template. See commit 2fda28214."""
        system_prompt = render_system_prompt(
            make_product(
                metadata={
                    "description": 'A {braced} description with {"json": true}',
                    "legitimate_examples": ["Why does {user} appear in my path?"],
                }
            )
        )
        self.assertIn('A {braced} description with {"json": true}', system_prompt)
        self.assertIn("- Why does {user} appear in my path?", system_prompt)


class UncertainRelevanceConfidenceCeilingTests(SimpleTestCase):
    """The ceiling only helps if it lands in the band that routes to a human reviewer."""

    def test_ceiling_sits_between_the_action_thresholds(self):
        self.assertGreater(UNCERTAIN_RELEVANCE_CONFIDENCE_CEILING, LOW_CONFIDENCE_THRESHOLD)
        self.assertLess(UNCERTAIN_RELEVANCE_CONFIDENCE_CEILING, HIGH_CONFIDENCE_THRESHOLD)

    def test_capped_confidence_is_flagged_for_review(self):
        action = determine_action_from_spam_result(
            {"confidence": UNCERTAIN_RELEVANCE_CONFIDENCE_CEILING}
        )
        self.assertEqual(action, ModerationAction.FLAG_REVIEW)


class CappedConfidenceRoutingTests(TestCase):
    """A capped product relevance verdict must reach a moderator, not auto-spam the question."""

    def setUp(self):
        self.user = User.objects.create_user(username="asker", email="asker@example.com")
        self.product = Product.objects.create(title="Firefox", slug="firefox", display_order=1)
        self.question = Question.objects.create(
            title=ISSUE_3090_QUESTION["subject"],
            content=ISSUE_3090_QUESTION["content"],
            creator=self.user,
            product=self.product,
        )
        self.spam_result = {
            "is_spam": True,
            "confidence": UNCERTAIN_RELEVANCE_CONFIDENCE_CEILING,
            "reason": "Unsure whether Firefox has a weather widget.",
            "maybe_misclassified": False,
        }

    def classify(self):
        process_classification_result(
            self.question,
            {
                "action": determine_action_from_spam_result(self.spam_result),
                "spam_result": self.spam_result,
            },
        )

    def test_capped_confidence_flags_for_review_without_marking_spam(self):
        self.classify()

        self.question.refresh_from_db()
        self.assertFalse(self.question.is_spam)

        flag = FlaggedObject.objects.get(
            content_type=ContentType.objects.get_for_model(Question),
            object_id=self.question.id,
        )
        self.assertEqual(flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(flag.reason, FlaggedObject.REASON_SPAM)
        self.assertIn("weather widget", flag.notes)

    def test_flagged_for_review_reaches_the_moderation_queue(self):
        self.classify()

        pending_for_moderators = get_flagged_objects(
            exclude_reason=FlaggedObject.REASON_CONTENT_MODERATION
        )
        self.assertEqual([flag.object_id for flag in pending_for_moderators], [self.question.id])

        # The stale queue processor only re-runs content moderation flags, so it must not
        # pick this one back up and classify it again.
        self.assertFalse(
            FlaggedObject.objects.filter(
                status=FlaggedObject.FLAG_PENDING,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
            ).exists()
        )
