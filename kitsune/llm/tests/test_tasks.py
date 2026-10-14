import json
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.test import override_settings
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from waffle.testutils import override_switch

from kitsune.customercare.models import SupportTicket
from kitsune.customercare.tests import SupportTicketFactory
from kitsune.customercare.utils import process_zendesk_classification_result
from kitsune.flagit.models import FlaggedObject
from kitsune.llm.spam.classifier import ModerationAction
from kitsune.llm.support.classifiers import classify_question, classify_zendesk_submission
from kitsune.llm.tasks import (
    assess_uncertain_spam,
    process_moderation_queue,
    question_classifier,
    queue_spam_assessment,
)
from kitsune.llm.tests import choice_answer, decision_answers
from kitsune.products.tests import (
    ProductFactory,
    ProductSupportConfigFactory,
    TopicFactory,
    ZendeskConfigFactory,
    ZendeskTopicConfigurationFactory,
    ZendeskTopicFactory,
)
from kitsune.questions.models import Question
from kitsune.questions.tests import AAQConfigFactory, QuestionFactory, QuestionLocaleFactory
from kitsune.questions.utils import process_classification_result
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile


@override_settings(
    QUESTION_CLASSIFIER_ENABLED=False,
    SPAM_REVIEW_PROBABILITY=0.50,
    SPAM_REJECT_PROBABILITY=0.80,
    SPAM_RELEVANCE_REVIEW_PROBABILITY=0.50,
    PRODUCT_REASSIGN_PROBABILITY=0.90,
    MOZILLA_ACCOUNT_REASSIGN_PROBABILITY=0.95,
)
class SupportClassificationTests(TestCase):
    def setUp(self):
        locale = QuestionLocaleFactory(locale="en-US")
        forum = AAQConfigFactory(enabled_locales=[locale])
        self.source = ProductFactory(title="Firefox", slug="firefox")
        self.target = ProductFactory(title="Firefox for Android", slug="mobile")
        self.source_config = ProductSupportConfigFactory(product=self.source, forum_config=forum)
        self.target_config = ProductSupportConfigFactory(product=self.target, forum_config=forum)
        self.old_topic = TopicFactory(
            title="Settings", products=[self.source], metadata={"description": "Desktop settings"}
        )
        self.new_topic = TopicFactory(
            title="Settings", products=[self.target], metadata={"description": "Android settings"}
        )
        self.question = QuestionFactory(
            product=self.source,
            topic=self.old_topic,
            tags=[self.old_topic.slug],
            locale="en-US",
            title="Firefox for Android settings",
            content="How can I change the Android browser settings?",
        )
        self.spam = self.enterContext(patch("kitsune.llm.spam.classifier.evaluate_decisions"))
        self.spam.return_value = decision_answers()
        self.routing = self.enterContext(
            patch("kitsune.llm.categorization.classifiers.evaluate_decisions")
        )
        self.routing.side_effect = [
            choice_answer("product", f"product:{self.target.pk}"),
            choice_answer("topic", f"topic:{self.new_topic.pk}"),
        ]

    def test_admitted_question_moves_and_uses_destination_topic_identity(self):
        self.assertEqual(self.question.product_slug, self.source.slug)
        result = classify_question(self.question)
        process_classification_result(self.question, result)
        self.assertEqual(self.question.product_slug, self.target.slug)
        self.question.refresh_from_db()
        self.assertEqual(self.question.product_id, self.target.pk)
        self.assertEqual(self.question.topic_id, self.new_topic.pk)
        self.assertFalse(self.question.is_spam)
        self.assertIn(self.new_topic.slug, self.question.tags.values_list("name", flat=True))

    def test_missing_selection_can_be_resolved_after_spam_screening(self):
        self.question.product = None
        self.question.topic = None
        self.question.save(update_fields=["product", "topic"])
        result = classify_question(self.question)
        process_classification_result(self.question, result)
        self.question.refresh_from_db()
        self.assertEqual(self.question.product_id, self.target.pk)
        self.assertEqual(self.question.topic_id, self.new_topic.pk)
        self.assertFalse(self.question.is_spam)

    def test_unresolved_missing_product_requires_routing_review_not_advisory_assessment(self):
        self.question.product = None
        self.question.topic = None
        self.question.save(update_fields=["product", "topic"])
        self.routing.side_effect = None
        self.routing.return_value = {
            "product": {
                "type": "choice",
                "name": "product",
                "choice": "unknown",
                "probabilities": [{"value": "unknown", "probability": 0.99}],
                "confidence": 0.99,
            }
        }
        result = classify_question(self.question)
        flag = process_classification_result(self.question, result)
        self.question.refresh_from_db()
        self.assertEqual(flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(flag.reason, FlaggedObject.REASON_CONTENT_MODERATION)
        self.assertIsNone(self.question.product_id)
        self.assertFalse(self.question.is_spam)
        self.assertIsNone(result["assessment_payload"])

    def test_clear_spam_does_not_change_product_or_topic(self):
        self.spam.return_value = decision_answers(0.95)
        result = classify_question(self.question)
        process_classification_result(self.question, result)
        self.question.refresh_from_db()
        self.assertTrue(self.question.is_spam)
        self.assertEqual(self.question.product_id, self.source.pk)
        self.assertEqual(self.question.topic_id, self.old_topic.pk)

    def test_uncertainty_preserves_routing_and_reaches_pending_review(self):
        self.spam.return_value = decision_answers(0.65)
        result = classify_question(self.question)
        flag = process_classification_result(self.question, result)
        self.question.refresh_from_db()
        self.assertEqual(flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(flag.reason, FlaggedObject.REASON_SPAM)
        self.assertFalse(self.question.is_spam)
        self.assertEqual(self.question.product_id, self.source.pk)
        self.assertEqual(self.question.topic_id, self.old_topic.pk)

    def test_a_destination_disabled_after_classification_is_not_applied(self):
        result = classify_question(self.question)
        self.target_config.is_active = False
        self.target_config.save(update_fields=["is_active"])
        with self.assertRaises(ValueError):
            process_classification_result(self.question, result)
        self.question.refresh_from_db()
        self.assertEqual(self.question.product_id, self.source.pk)
        self.assertEqual(self.question.topic_id, self.old_topic.pk)

    def test_missing_destination_id_cannot_clear_existing_routing(self):
        with self.assertRaises(ValueError):
            process_classification_result(
                self.question,
                {
                    "action": ModerationAction.NOT_SPAM,
                    "product_result": {"product_id": None},
                },
            )
        self.question.refresh_from_db()
        self.assertEqual(self.question.product_id, self.source.pk)
        self.assertEqual(self.question.topic_id, self.old_topic.pk)

    def test_foreign_topic_identity_cannot_be_assigned_to_current_product(self):
        with self.assertRaises(ValueError):
            process_classification_result(
                self.question,
                {
                    "action": ModerationAction.NOT_SPAM,
                    "topic_result": {"topic_id": self.new_topic.pk},
                },
            )
        self.question.refresh_from_db()
        self.assertEqual(self.question.topic_id, self.old_topic.pk)

    def test_ticket_moves_with_scoped_category_and_preserved_system_tags(self):
        self.source_config.zendesk_config = ZendeskConfigFactory()
        self.source_config.save()
        self.target_config.zendesk_config = ZendeskConfigFactory()
        self.target_config.save()
        category = ZendeskTopicFactory(topic=self.new_topic, slug="android-settings")
        ZendeskTopicConfigurationFactory(
            zendesk_config=self.target_config.zendesk_config, zendesk_topic=category
        )
        ticket = SupportTicketFactory(
            product=self.source,
            user=self.question.creator,
            category="desktop-settings",
            zendesk_tags=["loginless_ticket", "stage", "seg-original"],
            submission_status=SupportTicket.STATUS_PENDING,
        )
        result = classify_zendesk_submission(ticket)
        with patch("kitsune.customercare.utils.ZendeskClient") as client:
            client.return_value.create_ticket.return_value.ticket.id = "synthetic-ticket"
            process_zendesk_classification_result(ticket, result)
        ticket.refresh_from_db()
        self.assertEqual(ticket.product_id, self.target.pk)
        self.assertEqual(ticket.topic_id, self.new_topic.pk)
        self.assertEqual(ticket.category, category.slug)
        self.assertEqual(ticket.submission_status, SupportTicket.STATUS_SENT)
        self.assertTrue(
            {"loginless_ticket", "stage", "seg-original", "other"} <= set(ticket.zendesk_tags)
        )

    def test_deleted_ticket_owner_retains_current_product(self):
        self.source_config.zendesk_config = ZendeskConfigFactory()
        self.source_config.subscription_only = True
        self.source_config.save()
        ticket = SupportTicketFactory(product=self.source, user=self.question.creator)
        self.question.creator.delete()
        ticket.refresh_from_db()

        result = classify_zendesk_submission(ticket)

        self.assertEqual(result["action"], ModerationAction.NOT_SPAM)
        self.assertEqual(result["product_result"]["product_id"], self.source.pk)
        self.assertFalse(result["product_result"]["reassigned"])

    def test_spam_bypass_still_resolves_product_and_topic(self):
        self.spam.return_value = decision_answers(0.95)
        self.source_config.zendesk_config = ZendeskConfigFactory(skip_spam_moderation=True)
        self.source_config.save()
        self.target_config.zendesk_config = ZendeskConfigFactory()
        self.target_config.save()
        ticket = SupportTicketFactory(product=self.source, user=self.question.creator)
        result = classify_zendesk_submission(ticket)
        self.assertEqual(result["action"], ModerationAction.NOT_SPAM)
        self.assertEqual(result["product_result"]["product_id"], self.target.pk)
        self.assertEqual(result["topic_result"]["topic_id"], self.new_topic.pk)


@override_settings(QUESTION_CLASSIFIER_ENABLED=False)
class AdvisoryAssessmentTests(TestCase):
    def setUp(self):
        self.question = QuestionFactory(product=ProductFactory())
        self.payload = {
            "subject": self.question.title,
            "content": self.question.content,
            "channel": "forum",
            "locale": self.question.locale,
        }
        self.flag = process_classification_result(
            self.question,
            {
                "action": ModerationAction.FLAG_REVIEW,
                "spam_result": {"probability": 0.65, "relevance_uncertainty_probability": 0.1},
            },
        )
        self.notes = self.flag.notes
        with (
            patch("kitsune.llm.tasks.assess_uncertain_spam.delay") as queued,
            self.captureOnCommitCallbacks(execute=True),
        ):
            queue_spam_assessment(self.flag, {"assessment_payload": self.payload})
        self.task_args = queued.call_args.args
        self.assessment = {
            "verdict": "spam",
            "spam_signals": ["Promotional content."],
            "legitimate_signals": [],
            "uncertainty": "The author might be describing a support problem.",
        }

    def test_private_content_and_notes_are_not_serialized_as_task_arguments(self):
        ticket = SupportTicketFactory(
            subject="Private account issue 4de6",
            description="Private recovery details 3a94",
        )
        result = {
            "action": ModerationAction.FLAG_REVIEW,
            "spam_result": {"probability": 0.65, "relevance_uncertainty_probability": 0.1},
            "assessment_payload": {
                "subject": ticket.subject,
                "content": ticket.description,
                "channel": "ticket",
                "locale": "en-US",
            },
        }
        with (
            patch("kitsune.llm.tasks.assess_uncertain_spam.delay") as queued,
            self.captureOnCommitCallbacks(execute=True),
        ):
            process_zendesk_classification_result(ticket, result)
            self.assertFalse(queued.called)
        flag = FlaggedObject.objects.get(
            content_type=ContentType.objects.get_for_model(ticket), object_id=ticket.pk
        )
        serialized_arguments = json.dumps(queued.call_args.args)
        for private_text in (ticket.subject, ticket.description, flag.notes):
            self.assertNotIn(json.dumps(private_text)[1:-1], serialized_arguments)
        ticket.refresh_from_db()
        self.assertEqual(ticket.submission_status, SupportTicket.STATUS_FLAGGED)

    def test_advisory_is_applied_once_without_resolving_review(self):
        llm = RunnableLambda(lambda prompt: AIMessage(content=json.dumps(self.assessment)))
        with (
            patch.object(llm, "invoke", wraps=llm.invoke) as provider,
            patch("kitsune.llm.spam.classifier.get_llm", return_value=llm),
        ):
            assess_uncertain_spam(*self.task_args)
            self.flag.refresh_from_db()
            notes = self.flag.notes
            assess_uncertain_spam(*self.task_args)
        provider.assert_called_once()
        self.flag.refresh_from_db()
        self.question.refresh_from_db()
        self.assertEqual(self.flag.notes, notes)
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_PENDING)
        self.assertFalse(self.question.is_spam)

    def test_assessment_cannot_overwrite_a_moderators_concurrent_decision(self):
        def assess(payload):
            FlaggedObject.objects.filter(pk=self.flag.pk).update(
                status=FlaggedObject.FLAG_ACCEPTED, notes="Moderator decision"
            )
            return self.assessment

        with patch("kitsune.llm.tasks.assess_spam", side_effect=assess):
            assess_uncertain_spam(*self.task_args)
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_ACCEPTED)
        self.assertEqual(self.flag.notes, "Moderator decision")

    def test_assessment_cannot_replace_a_newer_pending_review(self):
        def assess(payload):
            FlaggedObject.objects.filter(pk=self.flag.pk).update(
                notes="New classification evidence"
            )
            return self.assessment

        with patch("kitsune.llm.tasks.assess_spam", side_effect=assess):
            assess_uncertain_spam(*self.task_args)
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(self.flag.notes, "New classification evidence")

    def test_provider_failure_leaves_review_intact(self):
        def fail(prompt):
            raise RuntimeError("Provider unavailable")

        with patch("kitsune.llm.spam.classifier.get_llm", return_value=RunnableLambda(fail)):
            with self.assertRaises(RuntimeError):
                assess_uncertain_spam(*self.task_args)
        self.flag.refresh_from_db()
        self.question.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(self.flag.notes, self.notes)
        self.assertFalse(self.question.is_spam)

    def test_edited_content_is_not_sent_for_an_old_assessment(self):
        self.question.content = "A corrected private support request"
        self.question.save(update_fields=["content"])
        with patch("kitsune.llm.tasks.assess_spam") as provider:
            assess_uncertain_spam(*self.task_args)
        provider.assert_not_called()
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(self.flag.notes, self.notes)


@override_settings(QUESTION_CLASSIFIER_ENABLED=False)
@override_switch("auto-question-classifier", active=True)
class ModerationQueueProcessingTestCase(TestCase):
    def setUp(self):
        self.question = QuestionFactory(product=ProductFactory())
        self.bot = Profile.get_sumo_bot()
        self.flag = self.pending_flag(self.question)
        self.classifier = self.enterContext(patch("kitsune.llm.tasks.classify_question"))
        self.classifier.return_value = {
            "action": ModerationAction.NOT_SPAM,
            "spam_result": {"probability": 0.1, "relevance_uncertainty_probability": 0.1},
        }

    def pending_flag(self, question):
        return FlaggedObject.objects.create(
            content_type=ContentType.objects.get_for_model(question),
            object_id=question.pk,
            creator=self.bot,
            reason=FlaggedObject.REASON_CONTENT_MODERATION,
            status=FlaggedObject.FLAG_PENDING,
        )

    def test_uncertain_reclassification_is_not_overwritten_as_accepted(self):
        self.classifier.return_value = {
            "action": ModerationAction.FLAG_REVIEW,
            "spam_result": {"probability": 0.65, "relevance_uncertainty_probability": 0.1},
        }
        process_moderation_queue()
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(self.flag.reason, FlaggedObject.REASON_SPAM)

    @override_switch("auto-question-classifier", active=False)
    def test_disabled_classifier_leaves_backlog_pending(self):
        process_moderation_queue()
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_PENDING)

    def test_unexpected_classifier_error_retains_existing_failure_handling(self):
        self.classifier.side_effect = RuntimeError("Classifier failure")
        process_moderation_queue()
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_REJECTED)

    def test_batch_limit_leaves_unprocessed_flags_pending(self):
        for _ in range(4):
            self.pending_flag(QuestionFactory(product=self.question.product))
        process_moderation_queue(batch_size=3)
        flags = FlaggedObject.objects.filter(creator=self.bot)
        self.assertEqual(flags.filter(status=FlaggedObject.FLAG_ACCEPTED).count(), 3)
        self.assertEqual(flags.filter(status=FlaggedObject.FLAG_PENDING).count(), 2)

    def test_unresolved_product_review_does_not_starve_later_backlog_items(self):
        product = self.question.product
        locale = QuestionLocaleFactory(locale="en-US")
        ProductSupportConfigFactory(
            product=product, forum_config=AAQConfigFactory(enabled_locales=[locale])
        )
        self.question.product = None
        self.question.save(update_fields=["product"])
        later_flag = self.pending_flag(QuestionFactory(product=product, locale="en-US"))
        self.classifier.side_effect = classify_question
        unknown_product = {
            "product": {
                "type": "choice",
                "name": "product",
                "choice": "unknown",
                "probabilities": [{"value": "unknown", "probability": 0.99}],
            }
        }
        with (
            patch(
                "kitsune.llm.spam.classifier.evaluate_decisions", return_value=decision_answers()
            ),
            patch(
                "kitsune.llm.categorization.classifiers.evaluate_decisions",
                return_value=unknown_product,
            ),
        ):
            process_moderation_queue(batch_size=1)
            process_moderation_queue(batch_size=1)
        self.flag.refresh_from_db()
        later_flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_PENDING)
        self.assertEqual(self.flag.reason, FlaggedObject.REASON_CONTENT_MODERATION)
        self.assertEqual(later_flag.status, FlaggedObject.FLAG_ACCEPTED)

    def test_reflagged_question_reenters_the_classification_backlog(self):
        process_moderation_queue()
        with (
            override_switch("auto-question-classifier", active=False),
            override_switch("flagit-spam-autoflag", active=True),
        ):
            question_classifier(self.question.pk)
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_PENDING)
        self.assertIsNone(self.flag.handled_by_id)
        process_moderation_queue()
        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_ACCEPTED)

    def test_removing_system_account_content_does_not_abort_the_batch(self):
        self.question.creator = self.bot
        self.question.save(update_fields=["creator"])
        question_id = self.question.pk
        later_flag = self.pending_flag(QuestionFactory(product=self.question.product))
        process_moderation_queue()
        later_flag.refresh_from_db()
        self.assertFalse(Question.objects.filter(pk=question_id).exists())
        self.assertEqual(later_flag.status, FlaggedObject.FLAG_ACCEPTED)
