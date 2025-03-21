from django.conf import settings

from kitsune.products.tests import ProductFactory
from kitsune.questions.handlers import AAQChain
from kitsune.questions.models import Answer, Question
from kitsune.questions.tests import (
    AnswerFactory,
    AnswerVoteFactory,
    QuestionFactory,
    QuestionVoteFactory,
)
from kitsune.sumo.tests import TestCase
from kitsune.users.models import Profile
from kitsune.users.tests import UserFactory


class TestSpamAAQHandler(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.sumo_bot = Profile.get_sumo_bot()
        self.chain = AAQChain()

    def test_spam_cleanup(self):
        """Test that spam questions and answers are deleted."""
        spam_q = QuestionFactory(creator=self.user, is_spam=True)
        spam_a = AnswerFactory(creator=self.user, is_spam=True)
        good_q = QuestionFactory(creator=self.user, is_spam=False)
        good_a = AnswerFactory(question=good_q, creator=self.user, is_spam=False)

        self.chain.run(self.user)

        self.assertFalse(Question.objects.filter(id=spam_q.id).exists())
        self.assertFalse(Answer.objects.filter(id=spam_a.id).exists())

        good_q.refresh_from_db()
        good_a.refresh_from_db()
        self.assertEqual(good_q.creator.username, self.sumo_bot.username)
        self.assertEqual(good_a.creator.username, self.sumo_bot.username)


class TestArchivedProductAAQHandler(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.sumo_bot = Profile.get_sumo_bot()
        self.chain = AAQChain()

    def test_archived_product_cleanup(self):
        """Test that questions and answers for archived products are deleted."""
        archived_product = ProductFactory(is_archived=True)
        active_product = ProductFactory(is_archived=False)
        archived_q = QuestionFactory(creator=self.user, product=archived_product)
        archived_a = AnswerFactory(question=archived_q, creator=self.user)
        active_q = QuestionFactory(creator=self.user, product=active_product)
        active_a = AnswerFactory(question=active_q, creator=self.user)

        self.chain.run(self.user)

        self.assertFalse(Question.objects.filter(id=archived_q.id).exists())
        self.assertFalse(Answer.objects.filter(id=archived_a.id).exists())

        active_q.refresh_from_db()
        active_a.refresh_from_db()
        self.assertEqual(active_q.creator.username, settings.SUMO_BOT_USERNAME)
        self.assertEqual(active_a.creator.username, settings.SUMO_BOT_USERNAME)


class TestOrphanedQuestionAAQHandler(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.sumo_bot = Profile.get_sumo_bot()
        self.chain = AAQChain()

    def test_orphaned_question_cleanup(self):
        """Test that questions without answers are deleted."""
        orphaned_q = QuestionFactory(creator=self.user)
        answered_q = QuestionFactory(creator=self.user)
        AnswerFactory(question=answered_q)

        self.chain.run(self.user)

        self.assertFalse(Question.objects.filter(id=orphaned_q.id).exists())

        answered_q.refresh_from_db()
        self.assertEqual(answered_q.creator.username, settings.SUMO_BOT_USERNAME)


class TestAAQChain(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.chain = AAQChain()
        self.sumo_bot = Profile.get_sumo_bot()

    def test_reassign_to_sumo_bot(self):
        """Test that remaining content is reassigned to SumoBot."""
        q = QuestionFactory(creator=self.user)
        a = AnswerFactory(creator=self.user, question=q)

        self.chain.run(self.user)

        q.refresh_from_db()
        a.refresh_from_db()
        self.assertEqual(q.creator.username, self.sumo_bot.username)
        self.assertEqual(a.creator.username, self.sumo_bot.username)

    def test_anonymize_votes(self):
        """Test that question and answer votes are anonymized."""
        av1 = AnswerVoteFactory()
        qv1 = QuestionVoteFactory()
        av2 = AnswerVoteFactory(creator=self.user)
        qv2 = QuestionVoteFactory(creator=self.user)

        self.chain.run(self.user)

        for obj in (av1, av2, qv1, qv2):
            obj.refresh_from_db()

        self.assertIs(av2.creator, None)
        self.assertTrue(av2.anonymous_id)
        self.assertIs(qv2.creator, None)
        self.assertTrue(qv2.anonymous_id)
        # The rest should remain untouched.
        self.assertTrue(av1.creator)
        self.assertFalse(av1.anonymous_id)
        self.assertTrue(qv1.creator)
        self.assertFalse(qv1.anonymous_id)

    def test_question_locking_and_notification(self):
        """
        Test that when a user is deleted:
        1. Their questions are reassigned to SumoBot
        2. Questions are locked
        3. An explanatory answer is added
        """
        # Create a question with an answer from another user
        question = QuestionFactory(creator=self.user)
        other_user = UserFactory()
        AnswerFactory(creator=other_user, question=question)

        self.chain.run(self.user)

        # Refresh from DB
        question.refresh_from_db()

        # Check question is reassigned and locked
        self.assertEqual(question.creator.username, self.sumo_bot.username)
        self.assertTrue(question.is_locked)

        # Verify the explanatory answer was added
        last_answer = question.answers.order_by("-created")[0]
        self.assertEqual(last_answer.creator.username, self.sumo_bot.username)
        self.assertIn(
            "locked because the original author has deleted their account", last_answer.content
        )

    def test_question_notification_when_already_locked(self):
        """
        Test that another explanatory answer is not added to a question that was
        already locked prior to its creator being deleted.
        """
        question = QuestionFactory(creator=self.user, is_locked=True)
        AnswerFactory(question=question)

        self.chain.run(self.user)

        # Refresh from DB
        question.refresh_from_db()

        # Check question is reassigned and locked
        self.assertEqual(question.creator.username, self.sumo_bot.username)
        self.assertTrue(question.is_locked)

        # Verify the explanatory answer was NOT added
        last_answer = question.answers.order_by("-created")[0]
        self.assertNotEqual(last_answer.creator.username, self.sumo_bot.username)
        self.assertNotIn(
            "locked because the original author has deleted their account", last_answer.content
        )
