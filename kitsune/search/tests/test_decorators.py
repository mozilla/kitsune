from django.db.models.signals import m2m_changed
from django.test.utils import override_settings

from kitsune.questions.models import Question
from kitsune.questions.tests import QuestionFactory
from kitsune.search.decorators import search_receiver
from kitsune.search.tests import Elastic7TestCase


class SearchReceiverTestCase(Elastic7TestCase):
    def setUp(self):
        @search_receiver(m2m_changed, Question.tags.through)
        def receiver(instance, **kwargs):
            raise AssertionError(f"function was called with action {kwargs['action']}")

        self.receiver = receiver

    def test_executes_function(self):
        with self.assertRaisesMessage(AssertionError, "function was called"):
            QuestionFactory(tags=["test"])

    @override_settings(ES_LIVE_INDEXING=False)
    def test_does_nothing_when_es_live_indexing_is_false(self):
        QuestionFactory(tags=["test"])

    def test_does_nothing_when_m2m_changed_action_is_pre(self):
        with self.assertRaisesMessage(AssertionError, "function was called with action post_add"):
            QuestionFactory(tags=["test"])
