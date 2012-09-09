from django.contrib.contenttypes.models import ContentType

from nose.tools import eq_

from flagit.tests import TestCaseBase
from flagit.models import FlaggedObject
from questions.models import Question
from questions.tests import question
from sumo.tests import post
from users.tests import user


class FlagTestCase(TestCaseBase):
    """Test the flag view."""
    def setUp(self):
        super(FlagTestCase, self).setUp()
        self.user = user(save=True)
        self.question = question(creator=self.user, save=True)

        self.client.login(username=self.user.username, password='testpass')

    def tearDown(self):
        super(FlagTestCase, self).tearDown()
        self.client.logout()

    def test_flag(self):
        """Flag a question."""
        d = {'content_type': ContentType.objects.get_for_model(Question).id,
             'object_id': self.question.id,
             'reason': 'spam',
             'next': self.question.get_absolute_url()}
        post(self.client, 'flagit.flag', d)
        eq_(1, FlaggedObject.objects.count())

        flag = FlaggedObject.objects.all()[0]
        eq_(self.user.username, flag.creator.username)
        eq_('spam', flag.reason)
        eq_(self.question, flag.content_object)
