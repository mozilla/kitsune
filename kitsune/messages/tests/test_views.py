from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.sumo.tests import LocalizingClient, TestCase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory


class ReadMessageTests(TestCase):
    def setUp(self):
        super(ReadMessageTests, self).setUp()
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.client.login(username=self.user1.username, password="testpass")

    def test_mark_bulk_message_read(self):
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1, message="foo")
        assert not i.read
        j = InboxMessage.objects.create(sender=self.user2, to=self.user1, message="foo")
        assert not j.read
        url = reverse("messages.bulk_action", locale="en-US")
        resp = self.client.post(url, {"id": [i.pk, j.pk], "mark_read": True}, follow=True)
        self.assertEqual(200, resp.status_code)
        assert InboxMessage.objects.get(pk=i.pk).read
        assert InboxMessage.objects.get(pk=j.pk).read

    def test_mark_bulk_read_none(self):
        url = reverse("messages.bulk_action", locale="en-US")
        resp = self.client.post(url, {"id": [], "mark_read": True}, follow=True)

        self.assertContains(resp, "No messages selected")

    def test_mark_message_read(self):
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1, message="foo")
        assert not i.read
        resp = self.client.get(reverse("messages.read", args=[i.pk]), follow=True)
        self.assertEqual(200, resp.status_code)
        assert InboxMessage.objects.get(pk=i.pk).read

    def test_unread_does_not_pin(self):
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1, message="foo", read=True)
        assert i.read
        resp = self.client.get(reverse("messages.read", args=[i.pk]), follow=True)
        self.assertEqual(200, resp.status_code)
        assert InboxMessage.objects.get(pk=i.pk).read

    def test_mark_message_replied(self):
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1, message="foo")
        assert not i.replied
        self.client.post(
            reverse("messages.new", locale="en-US"),
            {"to": self.user2.username, "message": "bar", "in_reply_to": i.pk},
        )
        assert InboxMessage.objects.get(pk=i.pk).replied


class DeleteMessageTests(TestCase):
    def setUp(self):
        super(DeleteMessageTests, self).setUp()
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.client.login(username=self.user1.username, password="testpass")

    def test_delete_inbox_message(self):
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1, message="foo")
        self.assertEqual(1, InboxMessage.objects.count())
        resp = self.client.post(
            reverse("messages.delete", args=[i.pk], locale="en-US"),
            {"confirmed": True},
            follow=True,
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, InboxMessage.objects.count())

    def test_delete_many_message(self):
        i = InboxMessage.objects.create(to=self.user1, sender=self.user2, message="foo")
        j = InboxMessage.objects.create(to=self.user1, sender=self.user2, message="foo")
        self.assertEqual(2, InboxMessage.objects.count())
        url = reverse("messages.bulk_action", locale="en-US")
        resp = self.client.post(
            url, {"id": [i.pk, j.pk], "delete": True, "confirmed": True}, follow=True
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, InboxMessage.objects.count())

    def test_delete_outbox_message(self):
        i = OutboxMessage.objects.create(sender=self.user1, message="foo")
        i.to.add(self.user2)
        self.assertEqual(1, OutboxMessage.objects.count())
        resp = self.client.post(
            reverse("messages.delete_outbox", args=[i.pk], locale="en-US"),
            {"confirmed": True},
            follow=True,
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, OutboxMessage.objects.count())

    def test_bulk_delete_none(self):
        url = reverse("messages.bulk_action", locale="en-US")
        resp = self.client.post(url, {"id": [], "delete": True}, follow=True)

        self.assertContains(resp, "No messages selected")


class OutboxTests(TestCase):
    client_class = LocalizingClient

    def setUp(self):
        super(OutboxTests, self).setUp()
        self.user1 = UserFactory()
        self.user2 = UserFactory()
        self.client.login(username=self.user1.username, password="testpass")

    def test_message_without_recipients(self):
        OutboxMessage.objects.create(sender=self.user1, message="foo")
        self.assertEqual(1, OutboxMessage.objects.count())
        resp = self.client.post(reverse("messages.outbox"), follow=True)
        self.assertEqual(200, resp.status_code)

    def test_delete_many_outbox_message(self):
        i = OutboxMessage.objects.create(sender=self.user1, message="foo")
        i.to.add(self.user2)
        j = OutboxMessage.objects.create(sender=self.user1, message="foo")
        j.to.add(self.user2)
        self.assertEqual(2, OutboxMessage.objects.count())
        url = reverse("messages.outbox_bulk_action", locale="en-US")
        resp = self.client.post(
            url, {"id": [i.pk, j.pk], "delete": True, "confirmed": True}, follow=True
        )
        self.assertEqual(200, resp.status_code)
        self.assertEqual(0, OutboxMessage.objects.count())
