from nose.tools import eq_

from messages import send_message
from messages.models import InboxMessage, OutboxMessage
from sumo.tests import TestCase, get_user


class SendTests(TestCase):
    """Tests for the internal send API."""

    fixtures = ['users.json']

    def test_send_message(self):
        to = [get_user('jsocol'), get_user('pcraciunoiu')]
        sender = get_user('rrosario')
        msg_text = "hi there!"
        send_message(to=to, text=msg_text, sender=sender)

        msgs_in = InboxMessage.objects.all()
        msgs_out = OutboxMessage.objects.all()
        eq_(1, msgs_out.count())
        msg_out = msgs_out[0]
        eq_(sender, msg_out.sender)
        eq_(msg_text, msg_out.message)
        for user in msg_out.to.all():
            assert user in to
        eq_(2, msgs_in.count())
        for message in msgs_in:
            eq_(sender, message.sender)
            assert message.to in to
            eq_(msg_text, message.message)
