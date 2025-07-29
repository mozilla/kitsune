from django.contrib.contenttypes.models import ContentType
from pyquery import PyQuery as pq

from kitsune.flagit.models import FlaggedObject
from kitsune.flagit.tests import TestCaseBase
from kitsune.questions.models import Answer
from kitsune.questions.tests import AnswerFactory
from kitsune.sumo.tests import get, post
from kitsune.users.tests import UserFactory, add_permission


class FlaggedQueueTestCase(TestCaseBase):
    """Test the flagit queue."""

    def setUp(self):
        super().setUp()
        self.answer = AnswerFactory()
        self.flagger = UserFactory()

        u = UserFactory()
        add_permission(u, FlaggedObject, "can_moderate")

        self.client.login(username=u.username, password="testpass")

    def tearDown(self):
        super().tearDown()
        self.client.logout()

    def test_queue(self):
        # Flag all answers
        num_answers = Answer.objects.count()
        for a in Answer.objects.all():
            f = FlaggedObject(content_object=a, reason="spam", creator_id=self.flagger.id)
            f.save()

        # Verify number of flagged objects
        response = get(self.client, "flagit.flagged_queue")
        doc = pq(response.content)
        self.assertEqual(num_answers, len(doc("#flagged-queue li.answer")))

        # Reject one flag
        content_type = ContentType.objects.get_for_model(Answer)
        flag = FlaggedObject.objects.filter(content_type=content_type).first()
        response = post(
            self.client, "flagit.update", {"status": FlaggedObject.FLAG_REJECTED}, args=[flag.id]
        )
        doc = pq(response.content)
        self.assertEqual(num_answers - 1, len(doc("#flagged-queue li.answer")))
