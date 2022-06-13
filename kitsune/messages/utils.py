from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.messages.signals import message_sent
from kitsune.messages.tasks import email_private_message
from kitsune.users.models import Setting


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
        if Setting.get_for_user(user, "email_private_messages"):
            email_private_message(inbox_message_id=im.id)

    message_sent.send(sender=InboxMessage, to=to, text=text, msg_sender=sender)


def unread_count_for(user):
    """Returns the number of unread messages for the specified user."""
    return InboxMessage.objects.filter(to=user, read=False).count()


def clear_inbox_and_outbox(user):
    """
    Delete the InboxMessage objects received and OutboxMessage objects sent by the
    given user. This does not affect the InboxMessage objects of the recipients of
    messages sent by this user.
    """
    InboxMessage.objects.filter(to=user).delete()
    OutboxMessage.objects.filter(sender=user).delete()
