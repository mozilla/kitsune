from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.messages.utils import send_message
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


class SendTests(TestCase):
    """Tests for the internal send API."""

    def test_send_message(self):
        to = UserFactory.create_batch(2)
        sender = UserFactory()
        msg_text = "hi there!"
        send_message(to=to, text=msg_text, sender=sender)

        msgs_in = InboxMessage.objects.all()
        msgs_out = OutboxMessage.objects.all()
        self.assertEqual(1, msgs_out.count())
        msg_out = msgs_out[0]
        self.assertEqual(sender, msg_out.sender)
        self.assertEqual(msg_text, msg_out.message)
        for u in msg_out.to.all():
            assert u in to
        self.assertEqual(2, msgs_in.count())
        for message in msgs_in:
            self.assertEqual(sender, message.sender)
            assert message.to in to
            self.assertEqual(msg_text, message.message)
