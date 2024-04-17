from django.contrib.auth.models import Group
from django.db.models import Prefetch
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
    # Prepare querysets for users and groups directly and efficiently
    users_qs = User.objects.filter(
        username__in=[obj.username for obj in to if isinstance(obj, User)]
    )
    groups_qs = Group.objects.filter(name__in=[obj.name for obj in to if isinstance(obj, Group)])

    # Prefetch group members and reduce DB hits
    groups_qs = groups_qs.prefetch_related(Prefetch("user_set"))

    # Resolve all unique users, including those in groups
    users = set(users_qs)
    for group in groups_qs:
        users.update(group.user_set.all())

    # Create the outbox message
    outbox_message = OutboxMessage.objects.create(sender=sender, message=text)
    outbox_message.to.set(users)
    outbox_message.to_group.set(groups_qs)

    # Fetch settings for email notifications in one go
    users_to_email = set(
        Setting.objects.filter(
            user__in=users, name="email_private_messages", value=True
        ).values_list("user__id", flat=True)
    )

    # Create inbox messages and handle emails
    for user in users:
        inbox_message = InboxMessage.objects.create(sender=sender, to=user, message=text)
        if user.id in users_to_email:
            email_private_message(inbox_message_id=inbox_message.id)

    # Send a signal if needed
    message_sent.send(sender=InboxMessage, to=to, text=text, msg_sender=sender)


def unread_count_for(user):
    """Returns the number of unread messages for the specified user."""
    return InboxMessage.objects.filter(to=user, read=False).count()
