from django.contrib.contenttypes.models import ContentType
from pyquery import PyQuery as pq

from kitsune.customercare.models import SupportTicket
from kitsune.flagit.models import FlaggedObject
from kitsune.flagit.tests import TestCaseBase
from kitsune.products.tests import ProductFactory
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

    def test_support_ticket_in_queue(self):
        """Test that flagged SupportTicket renders correctly in queue."""
        product = ProductFactory()
        ticket = SupportTicket.objects.create(
            subject="Test support ticket",
            description="This is a test ticket description",
            category="test-category",
            email="test@example.com",
            product=product,
            status=SupportTicket.STATUS_FLAGGED,
        )

        flag = FlaggedObject(content_object=ticket, reason="spam", creator_id=self.flagger.id)
        flag.save()

        response = get(self.client, "flagit.flagged_queue")
        self.assertEqual(200, response.status_code)

        content = response.content.decode("utf-8")
        self.assertIn("Test support ticket", content)
        self.assertIn("test@example.com", content)

    def test_content_type_filter(self):
        """Test filtering flagged queue by content type."""
        product = ProductFactory()
        ticket = SupportTicket.objects.create(
            subject="Unique spam ticket subject",
            description="Spam content",
            category="spam",
            email="spam@example.com",
            product=product,
            status=SupportTicket.STATUS_FLAGGED,
        )
        answer = AnswerFactory()

        FlaggedObject.objects.create(
            content_object=ticket, reason="spam", creator_id=self.flagger.id
        )
        FlaggedObject.objects.create(
            content_object=answer, reason="spam", creator_id=self.flagger.id
        )

        content_type = ContentType.objects.get_for_model(SupportTicket)
        from kitsune.sumo.urlresolvers import reverse

        url = f"{reverse('flagit.flagged_queue')}?content_type={content_type.id}"
        response = self.client.get(url, follow=True)
        self.assertEqual(200, response.status_code)

        content = response.content.decode("utf-8")
        self.assertIn("Unique spam ticket subject", content)
        self.assertNotIn(answer.content, content)
