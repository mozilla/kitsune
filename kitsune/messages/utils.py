from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.messages.signals import message_sent
from kitsune.messages.tasks import email_private_message
from kitsune.users.models import Setting


def send_message(to, to_group=None, text=None, sender=None):
    """Send a private message.

    :arg to: a list of Users to send the message to
    :arg to_group: a list of Groups to send the message to
    :arg sender: the User who is sending the message
    :arg text: the message text
    """
    # Initialize to_group to an empty list if None to avoid TypeErrors
    to_group = to_group or []
    to = to or []

    if sender:
        # Create the OutboxMessage with sender and text
        msg = OutboxMessage.objects.create(sender=sender, message=text)
        # Add recipients (Users)
        if to:
            msg.to.add(*to)
        # Add groups
        if to_group:
            msg.to_group.add(*to_group)

    # Send to individual users, not considering groups yet
    for user in to:
        # Create InboxMessage for each user, without setting to_group yet
        im = InboxMessage.objects.create(sender=sender, to=user, message=text)
        # Now add the groups
        im.to_group.add(*to_group)
        # Email notification if the user has opted in
        if Setting.get_for_user(user, "email_private_messages"):
            email_private_message(inbox_message_id=im.id)

    # Process each group separately to handle users within groups
    for group in to_group:
        for user in group.user_set.all():
            # Create InboxMessage for users in groups, without setting to_group yet
            im = InboxMessage.objects.create(sender=sender, to=user, message=text)
            # Now add the groups
            im.to_group.add(*to_group)
            # Email notification if the user has opted in
            if Setting.get_for_user(user, "email_private_messages"):
                email_private_message(inbox_message_id=im.id)

    # Send the signal after all messages have been processed
    message_sent.send(sender=InboxMessage, to=to, to_group=to_group, text=text, msg_sender=sender)


def unread_count_for(user):
    """Returns the number of unread messages for the specified user."""
    return InboxMessage.objects.filter(to=user, read=False).count()
