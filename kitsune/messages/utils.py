from django.contrib.auth.models import Group, User

from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.messages.signals import message_sent
from kitsune.messages.tasks import email_private_message
from kitsune.users.models import Setting


def send_message(to, text=None, sender=None):
    """Send a private message.
    :arg to: A dictionary with two keys, 'users' and 'groups',
            each containing a list usernames or group names.
    """

    # We need a sender, a message, and someone to send it to
    if not sender or not text or not to:
        return

    # Resolve all unique user ids, including those in groups
    # We need to keep group users separate for email notifications

    to_users = to.get("users", [])
    to_groups = to.get("groups", [])

    users = User.objects.filter(username__in=to_users)
    groups = Group.objects.filter(name__in=to_groups, profile__isnull=False)

    all_recipients_of_message = set(users.values_list("id", flat=True)) | set(
        User.objects.filter(groups__in=groups).values_list("id", flat=True)
    )

    # Create the outbox message
    outbox_message = OutboxMessage.objects.create(sender=sender, message=text)
    outbox_message.to.set(users)
    outbox_message.to_group.set(groups)

    # Fetch settings for email notifications in one go
    # For now, we only send emails to users who were individually
    # listed in 'to' field, not to users who are from groups
    users_to_email = set(
        Setting.objects.filter(
            user__in=users, name="email_private_messages", value=True
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
