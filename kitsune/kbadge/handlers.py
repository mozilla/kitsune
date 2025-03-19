from django.contrib.auth.models import User

from kitsune.kbadge.models import Award, Badge
from kitsune.users.handlers import UserDeletionListener
from kitsune.users.models import Profile


class BadgeListener(UserDeletionListener):
    """Handles badge cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        sumo_bot = Profile.get_sumo_bot()
        Badge.objects.filter(creator=user).update(creator=sumo_bot)


class AwardListener(UserDeletionListener):
    """Handles award cleanup when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        sumo_bot = Profile.get_sumo_bot()
        Award.objects.filter(creator=user).update(creator=sumo_bot)
