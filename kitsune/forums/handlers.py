from django.contrib.auth.models import User

from kitsune.forums.models import Post, Thread
from kitsune.users.handlers import UserDeletionListener
from kitsune.users.models import Profile


class ThreadListener(UserDeletionListener):
    """Handles thread cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        # First get all threads that should be reassigned, then delete the rest
        Thread.objects.filter(creator=user, replies__gt=0).update(creator=Profile.get_sumo_bot())
        Thread.objects.filter(creator=user).delete()


class PostListener(UserDeletionListener):
    """Handles post cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        Post.objects.filter(author=user).update(author=Profile.get_sumo_bot())
