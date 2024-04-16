from django.contrib.auth.models import Group

from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.users.models import User
from kitsune.messages.signals import message_sent

# from kitsune.messages.tasks import email_private_message
# from kitsune.users.models import Setting


def send_message(to, text=None, sender=None):
    """Send a private message.

    :arg to: Users or Groups to send the message to
    :arg sender: the User who is sending the message
    :arg text: the message text
    """

    # We need a sender, a message, and someone to send it to
    if not sender or not text or not to:
        return
    # This is users from the To field
    users = {user for user in to if isinstance(user, User)}
    # This is groups from the To field
    groups = {group for group in to if isinstance(group, Group)}
    # This is all the users that are going to receive the message
    receivers = users | set(User.objects.filter(groups__in=groups).distinct())

    outbox_message = OutboxMessage.objects.create(sender=sender, message=text)
    # Add the users from the To field to the outbox message, not all the users
    # that are going to receive the message - this way we don't overwhelm the
    # message UI
    outbox_message.to.set(users)

    if groups:
        # Add the groups from the To field to the message
        outbox_message.to_group.set(groups)

    # set_of_user_pks_to_email_private_message = set(
    #    Setting.objects.filter(
    #        user__in=receivers, name="email_private_messages", value=True
    #    ).values_list("user__pk", flat=True)
    # )

    for recipient in receivers:
        inbox_message = InboxMessage.objects.create(sender=sender, to=recipient, message=text)
        # If we had a user, and we made them an inbox message,
        # we should also add the groups to their message as well
        if groups:
            inbox_message.to_group.set(groups)
        # if recipient.pk in set_of_user_pks_to_email_private_message:
        #    email_private_message(inbox_message_id=inbox_message.id)

    message_sent.send(sender=InboxMessage, to=to, text=text, msg_sender=sender)


def unread_count_for(user):
    """Returns the number of unread messages for the specified user."""
    return InboxMessage.objects.filter(to=user, read=False).count()
