"""
Unit test for question sorting by views with null handling.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models import IntegerField, Value
from django.db.models.functions import Coalesce

from kitsune.questions.models import Question, QuestionVisits
from kitsune.products.models import Product


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
        order with nulls as 0."""
        # Apply the same logic as in the view
        question_qs = Question.objects.filter(
            id__in=[self.q_high_views.id, self.q_no_views.id, self.q_medium_views.id]
        )

        question_qs = question_qs.annotate(
            visits_nulls_as_zero=Coalesce(
                "questionvisits__visits", Value(0), output_field=IntegerField()
            )
        )
        question_qs = question_qs.order_by("-visits_nulls_as_zero")

        ordered_questions = list(question_qs)

        # Verify correct order: 500 views, 100 views, 0 views (null treated as 0)
        self.assertEqual(len(ordered_questions), 3)
        self.assertEqual(ordered_questions[0].id, self.q_high_views.id)
        self.assertEqual(ordered_questions[1].id, self.q_medium_views.id)
        self.assertEqual(ordered_questions[2].id, self.q_no_views.id)

        # Verify the annotated values
        self.assertEqual(getattr(ordered_questions[0], "visits_nulls_as_zero"), 500)
        self.assertEqual(getattr(ordered_questions[1], "visits_nulls_as_zero"), 100)
        self.assertEqual(getattr(ordered_questions[2], "visits_nulls_as_zero"), 0)
