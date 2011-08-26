import mock
import urllib
from multidb.middleware import PINNING_COOKIE
from nose.tools import eq_
import waffle.decorators

from messages.models import InboxMessage, OutboxMessage
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from users.tests import user


class ReadMessageTests(TestCase):
    def setUp(self):
        super(ReadMessageTests, self).setUp()
        self.user1 = user(save=True)
        self.user2 = user(save=True)
        self.client.login(username=self.user1.username, password='testpass')

    @mock.patch.object(waffle.decorators, 'flag_is_active')
    def test_mark_bulk_message_read(self, flag_is_active):
        flag_is_active.return_value = True
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo')
        assert not i.read
        j = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo')
        assert not j.read
        resp = self.client.post(reverse('messages.bulk_action', locale='en-US'),
                                {'id': [i.pk, j.pk], 'mark_read': True},
                                follow=True)
        eq_(200, resp.status_code)
        print resp
        assert InboxMessage.uncached.get(pk=i.pk).read
        assert InboxMessage.uncached.get(pk=j.pk).read

    @mock.patch.object(waffle.decorators, 'flag_is_active')
    def test_mark_message_read(self, flag_is_active):
        flag_is_active.return_value = True
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo')
        assert not i.read
        resp = self.client.get(reverse('messages.read', args=[i.pk]),
                               follow=True)
        eq_(200, resp.status_code)
        assert InboxMessage.uncached.get(pk=i.pk).read
        assert PINNING_COOKIE in resp.cookies

    @mock.patch.object(waffle.decorators, 'flag_is_active')
    def test_unread_does_not_pin(self, flag_is_active):
        flag_is_active.return_value = True
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo', read=True)
        assert i.read
        resp = self.client.get(reverse('messages.read', args=[i.pk]),
                               follow=True)
        eq_(200, resp.status_code)
        assert InboxMessage.uncached.get(pk=i.pk).read
        assert PINNING_COOKIE not in resp.cookies

    @mock.patch.object(waffle.decorators, 'flag_is_active')
    def test_mark_message_replied(self, flag_is_active):
        flag_is_active.return_value = True
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo')
        assert not i.replied
        resp = self.client.post(reverse('messages.new', locale='en-US'),
                                {'to': self.user2.username, 'message': 'bar',
                                 'in_reply_to': i.pk})
        assert InboxMessage.uncached.get(pk=i.pk).replied


class DeleteMessageTests(TestCase):
    def setUp(self):
        super(DeleteMessageTests, self).setUp()
        self.user1 = user(save=True)
        self.user2 = user(save=True)
        self.client.login(username=self.user1.username, password='testpass')

    @mock.patch.object(waffle.decorators, 'flag_is_active')
    def test_delete_inbox_message(self, flag_is_active):
        flag_is_active.return_value = True
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo')
        eq_(1, InboxMessage.objects.count())
        resp = self.client.post(reverse('messages.delete', args=[i.pk],
                                        locale='en-US'), follow=True)
        eq_(200, resp.status_code)
        eq_(0, InboxMessage.uncached.count())

    @mock.patch.object(waffle.decorators, 'flag_is_active')
    def test_delete_many_message(self, flag_is_active):
        flag_is_active.return_value = True
        i = InboxMessage.objects.create(to=self.user1, sender=self.user2,
                                        message='foo')
        j = InboxMessage.objects.create(to=self.user1, sender=self.user2,
                                        message='foo')
        eq_(2, InboxMessage.objects.count())
        url = '%s?%s' % (reverse('messages.bulk_delete', locale='en-US'),
                         urllib.urlencode({'id': [i.id, j.id]}, True))
        resp = self.client.post(url, follow=True)
        eq_(200, resp.status_code)
        eq_(0, InboxMessage.uncached.count())

    @mock.patch.object(waffle.decorators, 'flag_is_active')
    def test_delete_outbox_message(self, flag_is_active):
        flag_is_active.return_value = True
        i = OutboxMessage.objects.create(sender=self.user1, message='foo')
        i.to.add(self.user2)
        eq_(1, OutboxMessage.objects.count())
        resp = self.client.post(reverse('messages.delete_outbox', args=[i.pk],
                                        locale='en-US'), follow=True)
        eq_(200, resp.status_code)
        eq_(0, OutboxMessage.uncached.count())

    @mock.patch.object(waffle.decorators, 'flag_is_active')
    def test_delete_many_outbox_message(self, flag_is_active):
        flag_is_active.return_value = True
        i = OutboxMessage.objects.create(sender=self.user1, message='foo')
        i.to.add(self.user2)
        j = OutboxMessage.objects.create(sender=self.user1, message='foo')
        j.to.add(self.user2)
        eq_(2, OutboxMessage.objects.count())
        url = '%s?%s' % (reverse('messages.outbox_bulk_delete', locale='en-US'),
                         urllib.urlencode({'id': [i.id, j.id]}, True))
        resp = self.client.post(url, follow=True)
        eq_(200, resp.status_code)
        eq_(0, OutboxMessage.uncached.count())
