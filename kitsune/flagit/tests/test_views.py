from django.contrib.contenttypes.models import ContentType

from kitsune.flagit.models import FlaggedObject
from kitsune.flagit.tests import TestCaseBase
from kitsune.questions.models import Question
from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.tests import post
from kitsune.users.tests import UserFactory


class FlagTestCase(TestCaseBase):
    """Test the flag view."""

    def setUp(self):
        super(FlagTestCase, self).setUp()
        self.user = UserFactory()
        self.question = QuestionFactory(creator=self.user)

        self.client.login(username=self.user.username, password="testpass")

    def tearDown(self):
        super(FlagTestCase, self).tearDown()
        self.client.logout()

    def test_flag(self):
        """Flag a question."""
        d = {
            "content_type": ContentType.objects.get_for_model(Question).id,
            "object_id": self.question.id,
            "reason": "spam",
            "next": self.question.get_absolute_url(),
        }
        post(self.client, "flagit.flag", d)
        self.assertEqual(1, FlaggedObject.objects.count())

        flag = FlaggedObject.objects.all()[0]
        self.assertEqual(self.user.username, flag.creator.username)
        self.assertEqual("spam", flag.reason)
        self.assertEqual(self.question, flag.content_object)
