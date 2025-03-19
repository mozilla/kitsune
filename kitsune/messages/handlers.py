from django.contrib.auth.models import User

from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.users.handlers import UserDeletionListener
from kitsune.users.models import Profile


class MessageListener(UserDeletionListener):
    """Handles message cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        """
        When a user is deleted:
        - Delete their outbox messages
        - Keep inbox messages for other users and reassign them to SumoBot
        - Update outbox message recipients to SumoBot where the deleted user was a recipient
        """
        sumo_bot = Profile.get_sumo_bot()
        InboxMessage.objects.filter(to=user).delete()
        InboxMessage.objects.filter(sender=user).update(sender=sumo_bot)

        # Update outbox messages where the deleted user was a recipient
        outbox_messages = OutboxMessage.objects.filter(to=user)
        for message in outbox_messages:
            message.to.remove(user)
            message.to.add(sumo_bot)

        OutboxMessage.objects.filter(sender=user).delete()
