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

    def test_support_tickets_excluded_from_queue(self):
        """Test that SupportTickets do not appear in the main flagged queue."""
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
        self.assertNotIn("Test support ticket", content)
        self.assertNotIn("test@example.com", content)

    def test_support_ticket_not_in_filter(self):
        """Test that SupportTicket content type is not in the filter dropdown."""
        product = ProductFactory()

        # Create and flag a SupportTicket
        ticket = SupportTicket.objects.create(
            subject="Test ticket",
            description="Test description",
            category="test",
            email="test@example.com",
            product=product,
            status=SupportTicket.STATUS_FLAGGED,
        )
        FlaggedObject.objects.create(
            content_object=ticket, reason="spam", creator_id=self.flagger.id
        )

        response = get(self.client, "flagit.flagged_queue")
        self.assertEqual(200, response.status_code)

        content = response.content.decode("utf-8")

        # SupportTicket should not appear in the queue
        self.assertNotIn("Test ticket", content)

        # SupportTicket should not be in the content type filter dropdown
        ct_support_ticket = ContentType.objects.get_for_model(SupportTicket)
        self.assertNotIn(f'value="{ct_support_ticket.id}"', content)
