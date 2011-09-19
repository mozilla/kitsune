from multidb.middleware import PINNING_COOKIE
from nose.tools import eq_

from messages.models import InboxMessage, OutboxMessage
from sumo.tests import TestCase, LocalizingClient
from sumo.urlresolvers import reverse
from users.tests import user


class ReadMessageTests(TestCase):
    def setUp(self):
        super(ReadMessageTests, self).setUp()
        self.user1 = user(save=True)
        self.user2 = user(save=True)
        self.client.login(username=self.user1.username, password='testpass')

    def test_mark_message_read(self):
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo')
        assert not i.read
        resp = self.client.get(reverse('messages.read', args=[i.pk]),
                               follow=True)
        eq_(200, resp.status_code)
        assert InboxMessage.uncached.get(pk=i.pk).read
        assert PINNING_COOKIE in resp.cookies

    def test_unread_does_not_pin(self):
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo', read=True)
        assert i.read
        resp = self.client.get(reverse('messages.read', args=[i.pk]),
                               follow=True)
        eq_(200, resp.status_code)
        assert InboxMessage.uncached.get(pk=i.pk).read
        assert PINNING_COOKIE not in resp.cookies

    def test_mark_message_replied(self):
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo')
        assert not i.replied
        self.client.post(reverse('messages.new', locale='en-US'),
                         {'to': self.user2.username, 'message': 'bar',
                          'in_reply_to': i.pk})
        assert InboxMessage.uncached.get(pk=i.pk).replied


class DeleteMessageTests(TestCase):
    def setUp(self):
        super(DeleteMessageTests, self).setUp()
        self.user1 = user(save=True)
        self.user2 = user(save=True)
        self.client.login(username=self.user1.username, password='testpass')

    def test_delete_inbox_message(self):
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo')
        eq_(1, InboxMessage.objects.count())
        resp = self.client.post(reverse('messages.delete', args=[i.pk],
                                        locale='en-US'), follow=True)
        eq_(200, resp.status_code)
        eq_(0, InboxMessage.uncached.count())

    def test_delete_outbox_message(self):
        i = OutboxMessage.objects.create(sender=self.user1, message='foo')
        i.to.add(self.user2)
        eq_(1, OutboxMessage.objects.count())
        resp = self.client.post(reverse('messages.delete_outbox', args=[i.pk],
                                        locale='en-US'), follow=True)
        eq_(200, resp.status_code)
        eq_(0, OutboxMessage.uncached.count())


class OutboxTests(TestCase):
    client_class = LocalizingClient

    def test_message_without_recipients(self):
        self.user1 = user(save=True)
        self.client.login(username=self.user1.username, password='testpass')
        OutboxMessage.objects.create(sender=self.user1, message='foo')
        eq_(1, OutboxMessage.objects.count())
        resp = self.client.post(reverse('messages.outbox'), follow=True)
        eq_(200, resp.status_code)
