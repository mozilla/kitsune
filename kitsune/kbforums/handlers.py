from django.conf import settings
from django.contrib.auth.models import User

from kitsune.kbforums.models import Post, Thread
from kitsune.users.handlers import UserDeletionListener


class ThreadListener(UserDeletionListener):
    """Handles thread cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:

        sumo_bot = User.objects.get(username=settings.SUMO_BOT_USERNAME)
        Thread.objects.filter(creator=user).update(creator=sumo_bot)


class PostListener(UserDeletionListener):
    """Handles post cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:

        sumo_bot = User.objects.get(username=settings.SUMO_BOT_USERNAME)
        Post.objects.filter(creator=user).update(creator=sumo_bot)
