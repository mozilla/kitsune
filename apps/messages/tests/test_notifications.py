from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail

import mock
from nose.tools import eq_

from kbforums.events import NewPostEvent, NewThreadEvent
from kbforums.models import Thread, Post
from kbforums.tests import KBForumTestCase
from sumo.tests import post, attrs_eq, starts_with
from users.models import Setting
from wiki.models import Document

PRIVATE_MESSAGE_EMAIL = '{ sender } sent you the following'


class NotificationsTests(KBForumTestCase):
    """Test that notifications get sent."""

    @mock.patch.object(Site.objects, 'get_current')
    def test_private_message_sends_email(self, get_current):
        """
        With the setting enabled and receiving a private message should
        send and email.
        """
        get_current.return_value.domain = 'testserver'

        self.client.login(username='jsocol', password='testpass')
        user = User.objects.all()[0]
        res = post(self.client, 'messages.new',
             {'to': user.id, 'content': 'a message'})
        subject = u'You have a new private message from [{sender}]'

        attrs_eq(mail.outbox[0], to=[user.email],
                 subject=subject.format(sender=user.username))
        starts_with(mail.outbox[0].body,
                    PRIVATE_MESSAGE_EMAIL.format(sender=user.username))
