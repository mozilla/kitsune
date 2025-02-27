from django.conf import settings
from django.contrib.auth.models import User

from kitsune.gallery.models import Image, Video
from kitsune.users.handlers import UserDeletionListener


class MediaListener(UserDeletionListener):
    """Listener to transfer media to SumoBot when a user is deleted."""

    def on_user_deletion(self, user: User) -> None:
        """Handle the deletion of a user."""

        try:
            sumo_bot = User.objects.get(username=settings.SUMO_BOT_USERNAME)
        except User.DoesNotExist:
            raise ValueError("SumoBot user not found")
        else:
            Image.objects.filter(creator=user).update(creator=sumo_bot)
            Video.objects.filter(creator=user).update(creator=sumo_bot)
