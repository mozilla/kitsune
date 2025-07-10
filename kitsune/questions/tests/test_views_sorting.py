"""
Unit test for question sorting by views with null handling.
"""

from django.contrib.auth.models import User
from django.db.models import F
from django.test import TestCase

from kitsune.products.models import Product
from kitsune.questions.models import Question, QuestionVisits


class QuestionViewsSortingTestCase(TestCase):
    """Test question sorting by views handles null values correctly."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )

        self.product = Product.objects.create(
            title="Test Product",
            slug="test-product",
            description="Test product for testing",
            display_order=1,
        )

        # Create test questions with different view counts
        self.q_high_views = Question.objects.create(
            title="Question with 500 views",
            content="High views content",
            creator=self.user,
            product=self.product,
        )

        self.q_no_views = Question.objects.create(
            title="Question with no views",
            content="No views content",
            creator=self.user,
            product=self.product,
        )

        self.q_medium_views = Question.objects.create(
            title="Question with 100 views",
            content="Medium views content",
            creator=self.user,
            product=self.product,
        )

        # Add visit data (q_no_views intentionally has none to test null handling)
        QuestionVisits.objects.create(question=self.q_high_views, visits=500)
        QuestionVisits.objects.create(question=self.q_medium_views, visits=100)

    def test_views_sorting_descending(self):
        """Test that questions are sorted correctly by views in descending
        order with nulls at the end."""
        # Apply the same logic as in the view
        question_qs = Question.objects.filter(
            id__in=[self.q_high_views.id, self.q_no_views.id, self.q_medium_views.id]
        )

        # Use Django's built-in NULL sorting features
        question_qs = question_qs.order_by(F("questionvisits__visits").desc(nulls_last=True))

        ordered_questions = list(question_qs)

        # Verify correct order: 500 views, 100 views, NULL views (nulls at the end)
        self.assertEqual(len(ordered_questions), 3)
        self.assertEqual(ordered_questions[0].id, self.q_high_views.id)
        self.assertEqual(ordered_questions[1].id, self.q_medium_views.id)
        self.assertEqual(ordered_questions[2].id, self.q_no_views.id)

        # Verify the visit counts
        self.assertEqual(ordered_questions[0].num_visits, 500)
        self.assertEqual(ordered_questions[1].num_visits, 100)
        self.assertIsNone(ordered_questions[2].num_visits)
