from datetime import timedelta

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.utils import timezone
from parameterized import parameterized

from kitsune.questions.admin import QuestionAdmin
from kitsune.questions.models import Question
from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.tests import TestCase


class QuestionAdminSearchTests(TestCase):
    def setUp(self):
        self.old = QuestionFactory(
            title="needle old", created=timezone.now() - timedelta(days=200)
        )
        self.recent = QuestionFactory(title="needle recent")
        self.decoy = QuestionFactory(title=f"question {self.old.pk}")

    @parameterized.expand(
        [
            (
                "id_finds_that_question_only",
                lambda test: f" {test.old.pk} ",
                lambda test: {test.old},
            ),
            ("id_out_of_range", lambda test: "9" * 40, lambda test: set()),
            ("title_searches_recent_questions", lambda test: "needle", lambda test: {test.recent}),
        ]
    )
    def test_search(self, _name, term, expected):
        model_admin = QuestionAdmin(Question, AdminSite())

        results, _ = model_admin.get_search_results(
            RequestFactory().get("/"), Question.objects.all(), term(self)
        )

        self.assertEqual(set(results), expected(self))
