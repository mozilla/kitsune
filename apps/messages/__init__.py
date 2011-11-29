from messages.models import InboxMessage, OutboxMessage
from messages.signals import message_sent
from messages.tasks import email_private_message


def send_message(to, text, sender=None):
    """Send a private message.

    :arg to: a list of Users to send the message to
    :arg sender: the User who is sending the message
    :arg text: the message text
    """
    if sender:
        msg = OutboxMessage.objects.create(sender=sender, message=text)
        msg.to.add(*to)
    for user in to:
        im = InboxMessage.objects.create(sender=sender, to=user, message=text)
        email_private_message(inbox_message=im)

    message_sent.send(sender=InboxMessage, to=to, text=text,
                      msg_sender=sender)


def unread_count_for(user):
    """Returns the number of unread messages for the specified user."""
    return InboxMessage.objects.filter(to=user, read=False).count()
