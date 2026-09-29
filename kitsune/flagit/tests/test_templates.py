from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from pyquery import PyQuery as pq

from kitsune.customercare.models import SupportTicket
from kitsune.flagit.models import FlaggedObject
from kitsune.flagit.tests import TestCaseBase
from kitsune.products.tests import ProductFactory, TopicFactory
from kitsune.questions.models import Answer, Question
from kitsune.questions.tests import AnswerFactory, QuestionFactory
from kitsune.sumo.tests import get, post, translated_db_strings
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
            submission_status=SupportTicket.STATUS_FLAGGED,
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
            submission_status=SupportTicket.STATUS_FLAGGED,
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

    def test_moderation_topic_dropdowns_render_localized_titles_as_text(self):
        product = ProductFactory()
        parent = TopicFactory(title="Parent", products=[product])
        topic = TopicFactory(title="Child", parent=parent, products=[product])
        question = QuestionFactory(product=product, topic=topic)
        ticket = SupportTicket.objects.create(
            subject="Test ticket",
            description="Test description",
            category="test",
            email="test@example.com",
            product=product,
            topic=topic,
            submission_status=SupportTicket.STATUS_FLAGGED,
        )
        for content_object in (question, ticket):
            FlaggedObject.objects.create(
                content_object=content_object,
                reason=FlaggedObject.REASON_CONTENT_MODERATION,
                creator=self.flagger,
            )
        moderator = UserFactory()
        staff_group, _ = Group.objects.get_or_create(name=settings.STAFF_GROUP)
        moderator.groups.add(staff_group)
        add_permission(moderator, Question, "change_question")
        add_permission(moderator, SupportTicket, "change_supportticket")
        self.client.login(username=moderator.username, password="testpass")
        title = "<img src=x onerror=alert(1)> & recovery"

        with translated_db_strings("de", {("DB: products.Topic.title", "Child"): title}):
            response = get(self.client, "flagit.moderate_content", locale="de")

        self.assertEqual(200, response.status_code)
        options = pq(response.content)(f'select.topic-dropdown option[value="{topic.id}"]')
        self.assertEqual(2, len(options))
        for option in options.items():
            self.assertEqual(title, option.text().strip())
            self.assertEqual(0, len(option.find("img")))
        self.assertEqual(2, response.content.count(b"&nbsp;&nbsp;&nbsp;&nbsp;&lt;img src=x"))
