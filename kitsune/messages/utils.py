from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.users.models import User
from kitsune.messages.signals import message_sent
from kitsune.messages.tasks import email_private_message
from kitsune.users.models import Setting


def send_message(to, to_group=None, text=None, sender=None):
    """Send a private message.

    :arg to: a list of Users to send the message to
    :arg to_groups: Groups to send the message to
    :arg sender: the User who is sending the message
    :arg text: the message text
    """
    if not sender or not text:
        return

    # Assuming OutboxMessage doesn't necessarily need to be created for every recipient
    if to:
        outbox_message = OutboxMessage.objects.create(sender=sender, message=text)
        outbox_message.to.set(to)
        if to_group:
            outbox_message.to_group.set(to_group)

    for recipient in to:
        if isinstance(recipient, User):
            inbox_message = InboxMessage.objects.create(sender=sender, to=recipient, message=text)
            # If we had a user, and we made them an inbox message,
            # we should also add the to_groups to their message as well
            if to_group:
                inbox_message.to_group.set(to_group)
            if Setting.get_for_user(recipient, "email_private_messages"):
                email_private_message(inbox_message_id=inbox_message.id)

    message_sent.send(sender=InboxMessage, to=to, to_group=to_group, text=text, msg_sender=sender)


def unread_count_for(user):
    """Returns the number of unread messages for the specified user."""
    return InboxMessage.objects.filter(to=user, read=False).count()
