from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.users.models import User
from kitsune.messages.signals import message_sent
from kitsune.messages.tasks import email_private_message
from kitsune.users.models import Setting


def send_message(to, text=None, sender=None):
    """Send a private message.

    :arg to: Users or Groups to send the message to
    :arg sender: the User who is sending the message
    :arg text: the message text
    """

    # We need a sender, a message, and someone to send it to
    if not sender or not text or not to:
        return
    # User pks from users in To field
    users = []
    groups = []

    for obj in to:
        if isinstance(obj, User):
            users.append(obj)
        else:
            groups.append(obj)

    # User pks from to field users
    to_users = set(User.objects.filter(username__in=users).values_list("id", flat=True))

    # Group users' pks only - could be a lot of them
    group_users = set(User.objects.filter(groups__in=groups).values_list("id", flat=True))

    # Resolve all unique user ids, including those in groups
    # We need to keep group_users separate for email notifications
    all_recipients_of_message = to_users.union(group_users)

    # Create the outbox message
    outbox_message = OutboxMessage.objects.create(sender=sender, message=text)
    to_users = User.objects.filter(id__in=to_users)
    outbox_message.to.set(to_users)
    outbox_message.to_group.set(groups)

    # Fetch settings for email notifications in one go
    # For now, we only send emails to users who were individually
    # listed in 'to' field, not to users who are from groups
    users_to_email = set(
        Setting.objects.filter(
            user__in=to_users, name="email_private_messages", value=True
        ).values_list("user__id", flat=True)
    )

    # Create inbox messages and handle emails
    inbox_messages = [
        InboxMessage(sender=sender, to_id=user_id, message=text)
        for user_id in all_recipients_of_message
    ]

    recipient_id_to_message_id = {
        msg.to_id: msg.id for msg in InboxMessage.objects.bulk_create(inbox_messages)
    }

    # Assuming messages are fetched again with IDs if necessary
    for user_id in users_to_email:
        if message_id := recipient_id_to_message_id.get(user_id):
            email_private_message.delay(inbox_message_id=message_id)

    # Send a signal if needed
    message_sent.send(sender=InboxMessage, to=to, text=text, msg_sender=sender)


def unread_count_for(user):
    """Returns the number of unread messages for the specified user."""
    return InboxMessage.objects.filter(to=user, read=False).count()
