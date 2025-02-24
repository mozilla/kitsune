from django.conf import settings
from django.contrib.auth.models import User

from kitsune.messages.models import InboxMessage, OutboxMessage
from kitsune.users.handlers import UserDeletionListener


class MessageListener(UserDeletionListener):
    """Handles message cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        """
        When a user is deleted:
        - Delete their outbox messages
        - Keep inbox messages for other users and reassign them to SumoBot
        """
        try:
            sumo_bot = User.objects.get(username=settings.SUMO_BOT_USERNAME)
        except User.DoesNotExist:
            raise ValueError("SumoBot user not found")

        InboxMessage.objects.filter(to=user).delete()
        InboxMessage.objects.filter(sender=user).update(sender=sumo_bot)
        OutboxMessage.objects.filter(sender=user).delete()
