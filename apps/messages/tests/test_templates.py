from nose.tools import eq_
from pyquery import PyQuery as pq

from messages.models import OutboxMessage
from sumo.helpers import urlparams
from sumo.tests import TestCase
from sumo.urlresolvers import reverse
from users.tests import user


class SendMessageTestCase(TestCase):
    def setUp(self):
        super(SendMessageTestCase, self).setUp()
        self.user1 = user(save=True)
        self.user2 = user(save=True)
        self.user3 = user(save=True)
        self.client.login(username=self.user1.username, password='testpass')

    def test_send_message_page(self):
        # Make sure page loads.
        response = self.client.get(reverse('messages.new'), follow=True)
        eq_(200, response.status_code)
        assert len(pq(response.content)('#id_message'))

    def _test_send_message_to(self, to):
        # Post a new message and verify it was sent.
        data = {'to': to, 'message': 'hi there'}
        response = self.client.post(reverse('messages.new', locale='en-US'),
                                    data, follow=True)
        eq_(200, response.status_code)
        eq_('Your message was sent!',
            pq(response.content)('ul.user-messages').text())
        eq_(1, OutboxMessage.objects.filter(sender=self.user1).count())
        return response

    def test_send_message_to_one(self):
        self._test_send_message_to(self.user2.username)

    def test_send_message_to_two(self):
        to = ', '.join([self.user2.username, self.user3.username])
        self._test_send_message_to(to)

    def test_send_message_trailing_comma(self):
        self._test_send_message_to(self.user2.username + ',')

    def test_send_message_two_commas(self):
        self._test_send_message_to(self.user2.username + ',,' +
                                   self.user3.username)

    def test_send_message_to_prefilled(self):
        url = urlparams(reverse('messages.new'), to=self.user2.username)
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        eq_(self.user2.username,
            pq(response.content)('#id_to')[0].attrib['value'])

    def test_no_markup_in_message_list(self):
        response = self._test_send_message_to(self.user2.username)
        eq_(pq(response.content)('read').text(),
            pq(response.content)('read').html())

    def test_send_message_ratelimited(self):
        """Verify that after 50 messages, no more are sent."""
        # Try to send 53 messages.
        for i in range(53):
            self.client.post(
                reverse('messages.new', locale='en-US'),
                {'to': self.user2.username, 'message': 'hi there %s' % i})

        # Verify only 50 are sent.
        eq_(50, OutboxMessage.objects.filter(sender=self.user1).count())


class MessagePreviewTests(TestCase):
    """Tests for preview."""
    def setUp(self):
        super(MessagePreviewTests, self).setUp()
        self.user = user(save=True)
        self.client.login(username=self.user.username, password='testpass')

    def test_preview(self):
        """Preview the wiki syntax content."""
        response = self.client.post(
            reverse('messages.preview_async', locale='en-US'),
            {'content': '=Test Content='}, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Test Content', doc('div.message h1').text())
