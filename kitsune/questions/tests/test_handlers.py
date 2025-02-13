from django.conf import settings
from django.contrib.auth.models import User

from kitsune.products.tests import ProductFactory
from kitsune.questions.handlers import AAQChain
from kitsune.questions.models import Answer, Question
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class TestSpamAAQHandler(TestCase):
    def setUp(self):
        self.user = UserFactory()
        User.objects.get_or_create(username=settings.SUMO_BOT_USERNAME)
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
        self.assertEqual(good_q.creator.username, settings.SUMO_BOT_USERNAME)
        self.assertEqual(good_a.creator.username, settings.SUMO_BOT_USERNAME)


class TestArchivedProductAAQHandler(TestCase):
    def setUp(self):
        self.user = UserFactory()
        User.objects.get_or_create(username=settings.SUMO_BOT_USERNAME)
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
        User.objects.get_or_create(username=settings.SUMO_BOT_USERNAME)
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

    def test_missing_sumo_bot(self):
        """Test that chain raises ValueError when SumoBot user doesn't exist."""

        with self.assertRaises(ValueError):
            self.chain.run(self.user)

    def test_reassign_to_sumo_bot(self):
        """Test that remaining content is reassigned to SumoBot."""
        User.objects.get_or_create(username=settings.SUMO_BOT_USERNAME)
        q = QuestionFactory(creator=self.user)
        a = AnswerFactory(creator=self.user, question=q)

        self.chain.run(self.user)

        q.refresh_from_db()
        a.refresh_from_db()
        self.assertEqual(q.creator.username, settings.SUMO_BOT_USERNAME)
        self.assertEqual(a.creator.username, settings.SUMO_BOT_USERNAME)
