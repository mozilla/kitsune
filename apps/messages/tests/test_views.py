import mock
from nose.tools import eq_
import waffle.decorators

from messages.models import InboxMessage
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
    def test_mark_message_read(self, flag_is_active):
        flag_is_active.return_value = True
        i = InboxMessage.objects.create(sender=self.user2, to=self.user1,
                                        message='foo')
        i.save()
        assert not i.read
        resp = self.client.get(reverse('messages.read', args=[i.pk]),
                               follow=True)
        eq_(200, resp.status_code)
        assert InboxMessage.uncached.get(pk=i.pk).read
