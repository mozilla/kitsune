from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from kitsune.flagit.models import FlaggedObject
from kitsune.llm.tasks import process_moderation_queue
from kitsune.products.models import Product
from kitsune.questions.models import Question
from kitsune.users.models import Profile


class ModerationQueueProcessingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        Profile.objects.create(user=self.user)
        self.product = Product.objects.create(
            title="Test Product", slug="test-product", display_order=1
        )
        self.question = Question.objects.create(
            title="Test Question",
            content="Test content",
            creator=self.user,
            product=self.product,
        )
        self.content_type = ContentType.objects.get_for_model(Question)

        # Create a pending flagged object
        self.flag = FlaggedObject.objects.create(
            content_type=self.content_type,
            object_id=self.question.id,
            creator=self.user,
            reason=FlaggedObject.REASON_CONTENT_MODERATION,
            status=FlaggedObject.FLAG_PENDING,
        )

    @patch("kitsune.llm.tasks.waffle.switch_is_active")
    @patch("kitsune.llm.tasks.classify_question")
    @patch("kitsune.questions.utils.process_classification_result")
    def test_process_moderation_queue_success(self, mock_process, mock_classify, mock_switch):
        """Test that flagged objects are processed correctly."""
        mock_switch.return_value = True

        mock_result = {
            "action": "not_spam",
            "spam_result": {"is_spam": False, "confidence": 20},
            "topic_result": {"topic": "Test Topic", "reason": "Test reason"},
        }
        mock_classify.return_value = mock_result

        result = process_moderation_queue(batch_size=10)

        self.assertIn("Processed 1 stale flagged objects", result)

        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_ACCEPTED)
        self.assertIn("Processed by LLM stale queue processor", self.flag.notes)
        self.assertIn("Action: not_spam", self.flag.notes)

        mock_classify.assert_called_once_with(self.question)
        mock_process.assert_called_once_with(self.question, mock_result)

    @patch("kitsune.llm.tasks.waffle.switch_is_active")
    def test_process_moderation_queue_disabled(self, mock_switch):
        """Test that processing is skipped when waffle switch is disabled."""
        mock_switch.return_value = False

        result = process_moderation_queue(batch_size=10)

        self.assertIsNone(result)

        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_PENDING)

    @patch("kitsune.llm.tasks.waffle.switch_is_active")
    @patch("kitsune.llm.tasks.classify_question")
    def test_process_moderation_queue_error_handling(self, mock_classify, mock_switch):
        """Test error handling when LLM processing fails."""
        mock_switch.return_value = True
        mock_classify.side_effect = Exception("LLM API error")

        result = process_moderation_queue(batch_size=10)

        self.assertIn("Processed 0 stale flagged objects", result)

        self.flag.refresh_from_db()
        self.assertEqual(self.flag.status, FlaggedObject.FLAG_REJECTED)
        self.assertIn("Error processing through LLM", self.flag.notes)

    @patch("kitsune.llm.tasks.waffle.switch_is_active")
    @patch("kitsune.llm.tasks.classify_question")
    def test_process_moderation_queue_deleted_content(self, mock_classify, mock_switch):
        """Test handling of flagged objects where content was deleted."""
        mock_switch.return_value = True
        mock_classify.return_value = {}

        # Delete the question, which should also delete the flag
        flag_id = self.flag.id
        self.question.delete()

        result = process_moderation_queue(batch_size=10)
        self.assertIn("Processed 0 stale flagged objects", result)
        # The flag should be deleted, so check for DoesNotExist
        with self.assertRaises(FlaggedObject.DoesNotExist):
            FlaggedObject.objects.get(id=flag_id)

    def test_batch_size_limit(self):
        """Test that batch size limits the number of items processed."""
        # Create additional questions and flags
        for i in range(4):
            question = Question.objects.create(
                title=f"Test Question {i}",
                content=f"Test content {i}",
                creator=self.user,
                product=self.product,
            )
            FlaggedObject.objects.create(
                content_type=self.content_type,
                object_id=question.id,
                creator=self.user,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
                status=FlaggedObject.FLAG_PENDING,
            )

        with patch("kitsune.llm.tasks.waffle.switch_is_active", return_value=True):
            with patch("kitsune.llm.tasks.classify_question") as mock_classify:
                with patch("kitsune.questions.utils.process_classification_result"):
                    mock_classify.return_value = {
                        "action": "not_spam",
                        "spam_result": {"is_spam": False, "confidence": 20},
                        "topic_result": {"topic": "Test Topic", "reason": "Test reason"},
                    }

                    result = process_moderation_queue(batch_size=3)

                    self.assertIn("Processed 3 stale flagged objects", result)
                    self.assertEqual(mock_classify.call_count, 3)
