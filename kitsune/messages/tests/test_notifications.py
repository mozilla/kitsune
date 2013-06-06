from django.contrib.sites.models import Site
from django.core import mail

import mock

from kitsune.kbforums.tests import KBForumTestCase
from kitsune.sumo.tests import post, attrs_eq, starts_with
from kitsune.users.models import Setting
from kitsune.users.tests import user

PRIVATE_MESSAGE_EMAIL = '{sender} sent you the following'


class NotificationsTests(KBForumTestCase):
    """Test that notifications get sent."""

    def setUp(self):
        super(NotificationsTests, self).setUp()

        self.sender = user(username=u'Alice', save=True)
        self.to = user(username=u'Bob', save=True)

    @mock.patch.object(Site.objects, 'get_current')
    def test_private_message_sends_email(self, get_current):
        """
        With the setting enabled and receiving a private message should
        send and email.
        """
        get_current.return_value.domain = 'testserver'

        s, c = Setting.objects.get_or_create(user=self.to,
                                             name='email_private_messages')
        s.value = True
        s.save()
        # User has setting, and should recieve notification email.

        assert Setting.get_for_user(self.to, 'email_private_messages')

        self.client.login(username=self.sender.username, password='testpass')
        post(self.client, 'messages.new',
             {'to': self.to, 'message': 'a message'})
        subject = u'[SUMO] You have a new private message from [{sender}]'

        attrs_eq(mail.outbox[0], to=[self.to.email],
                 subject=subject.format(sender=self.sender.username))
        starts_with(mail.outbox[0].body,
                    PRIVATE_MESSAGE_EMAIL.format(sender=self.sender.username))

    @mock.patch.object(Site.objects, 'get_current')
    def test_private_message_not_sends_email(self, get_current):
        """
        With the setting not enabled and receiving a private message.
        The user should not get an email.
        """
        get_current.return_value.domain = 'testserver'

        s, c = Setting.objects.get_or_create(user=self.to,
                                             name='email_private_messages')
        # Now user should not recieve email.
        s.value = False
        s.save()
        assert not Setting.get_for_user(self.to, 'email_private_messages')

        self.client.login(username=self.sender.username, password='testpass')
        post(self.client, 'messages.new',
             {'to': self.to, 'message': 'a message'})

        assert not mail.outbox
